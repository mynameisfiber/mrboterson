import sqlite3
import ujson as json
from datetime import datetime


def format_pin(pin):
    header = ("[{rowid}] On {timestamp:%Y-%m-%d %H:%M:%S} " +
              "<@{user}> pinned to <#{channel_id}>").format(**pin)
    if '\n' in pin['display']:
        pin['display'] = '\n' + pin['display']
    return "{}: {}".format(header, pin['display'])


class PinDB(object):
    def __init__(self, db):
        self.db = sqlite3.connect(db)
        self.db.row_factory = dict_factory
        with self.db:
            self.db.execute('''CREATE TABLE IF NOT EXISTS pins (
                channel_id text,
                user text,
                timestamp real,
                msg_user text,
                display text,
                data text
            );''')

    def save_pins(self, pins, meta):
        for pin in pins:
            if 'fallback' in pin:
                idx = pin['fallback'].index('] ')
                if idx > 0:
                    pin['display'] = pin['fallback'][idx+1:]
                if 'user' not in pin:
                    pin['user'] = pin['author_subname']
            elif 'user' in pin:
                pin['display'] = "<@{user}>: {text}".format(**pin)
        users = ",".join(p['user'] for p in pins)
        with self.db:
            data = (
                meta['channel'],
                meta['user'],
                float(meta['ts']),
                users,
                '\n'.join(p['display'] for p in pins),
                json.dumps(pins),
            )
            self.db.execute("INSERT INTO pins VALUES (?,?,?,?,?,?)",
                            data)

    def get_pins(self, channel=None, pin_ids=None):
        cursor = self.db.cursor()
        if channel is not None:
            cursor.execute('SELECT rowid, * FROM pins WHERE channel_id=? ' +
                           'ORDER BY timestamp ASC', (channel,))
        elif pin_ids is not None:
            for pin in pin_ids:
                cursor.execute(
                    'SELECT rowid, * FROM pins WHERE rowid=?',
                    (pin,)
                )
        for pin in cursor:
            pin['timestamp'] = datetime.fromtimestamp(pin['timestamp'])
            yield pin
        cursor.close()

    def delete_pin(self, pin_id):
        with self.db:
            self.db.execute('DELETE FROM pins WHERE rowid=?', (pin_id,))


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
