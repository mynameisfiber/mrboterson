import sqlite3
from datetime import datetime


class PinDB(object):
    def __init__(self, db):
        self.db = sqlite3.connect(db)
        self.db.row_factory = dict_factory
        with self.db:
            self.db.execute('''CREATE TABLE IF NOT EXISTS pins (
                channel_id text,
                pin_user text,
                pin_timestamp real,
                msg_user text,
                message text,
                msg_timestamp real,
                link text
            );''')

    def save_pin(self, pin):
        data = (
            pin['channel_id'],
            pin['user'],
            float(pin['event_ts']),
            pin['item']['message']['user'],
            pin['item']['message']['text'],
            float(pin['item']['message']['ts']),
            pin['item']['message']['permalink'],

        )
        with self.db:
            self.db.execute("INSERT INTO pins VALUES (?, ?, ?, ?, ?, ?, ?)", data)

    def get_pins(self, channel):
        cursor = self.db.cursor()
        cursor.execute('SELECT rowid, * FROM pins WHERE channel_id=? ' +
                  'ORDER BY pin_timestamp ASC', (channel,))
        for pin in cursor:
            pin['msg_timestamp'] = datetime.fromtimestamp(pin['msg_timestamp'])
            pin['pin_timestamp'] = datetime.fromtimestamp(pin['pin_timestamp'])
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

