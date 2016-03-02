from slackclient import SlackClient
import ujson as json

import time
import os
import string
from datetime import datetime
from collections import defaultdict


def format_pin(pin):
    data = {
        "pin_user": pin['user'],
        "msg_user": pin['item']['message']['user'],
        "message": pin['item']['message']['text'],
        "date": datetime.fromtimestamp(float(pin['item']['message']['ts'])),
    }
    return ("On {date:%Y-%m-%d %H:%M:%S} " +
            "<@{pin_user}> pinned: " +
            "<@{msg_user}> : {message}").format(**data)


class MrBoterson(object):
    def __init__(self, token, username, userid, timeout=1):
        self.sc = SlackClient(token)
        self.username = username
        self.userid = userid
        self._at_mention = '<@{}>'.format(userid)
        self.timeout = timeout
        self.load_pins()

    def start(self):
        if self.sc.rtm_connect():
            while True:
                events = self.sc.rtm_read()
                self.dispatch_events(events)
                time.sleep(self.timeout)
        return False

    def dispatch_events(self, events):
        for event in events:
            if event['type'] == 'message' and \
                    event.get('text', '').startswith(self._at_mention):
                print("Dispatching @response")
                self.on_at_mention(event)
            elif event['type'] == 'pin_added':
                print("Dispatching pin")
                self.on_pin(event)

    def on_at_mention(self, event):
        strip = string.punctuation + ' '
        message = event['text'][len(self._at_mention):] \
            .strip(strip)
        # normalize the message
        message = ' '.join(m.strip(strip) for m in message.split(' '))
        if message.startswith('dance'):
            self.sc.api_call("chat.postMessage", channel=event['channel'],
                             text="└[∵┌]└[ ∵ ]┘[┐∵]┘", username=username)
        elif message.startswith('get pins'):
            channel = event['channel']
            for pin in self.get_pins(channel):
                self.sc.api_call("chat.postMessage", channel=event['channel'],
                                 text=format_pin(pin), username=username)
        else:
            self.sc.api_call("chat.postMessage", channel=event['channel'],
                             text="stop taking to me", username=username)

    def get_pins(self, channel):
        for timestamp, pin in self._pin_cache[channel].items():
            yield json.load(open(pin))

    def save_pin(self, pin):
        channel_id = pin['channel_id']
        timestamp = int(float(pin['event_ts']))
        pin_path = "./data/{}/{}.json".format(channel_id, timestamp)
        try:
            parent_path = os.path.dirname(pin_path)
            os.makedirs(parent_path, exist_ok=True)
        except IOError:
            raise
        else:
            json.dump(pin, open(pin_path, 'w+'))
            self._pin_cache[channel_id][timestamp] = pin_path

    def load_pins(self):
        cache = defaultdict(dict)
        for dirpath, _, fnames in os.walk('./data/'):
            if not fnames:
                continue
            dirname = dirpath.split('/')[-1]
            c = {}
            for fname in fnames:
                timestamp = fname.split('.')[0]
                filepath = os.path.join(dirpath, fname)
                c[timestamp] = filepath
            cache[dirname] = c
        self._pin_cache = cache

    def on_pin(self, event):
        if event['item']['type'] != 'message':
            self.sc.api_call(
                "chat.postMessage",
                channel=event['channel_id'],
                text="How insensitive... I only save text pins."
            )
        try:
            self.save_pin(event)
        except Exception as e:
            self.sc.api_call(
                "chat.postMessage",
                channel=event['channel_id'],
                text="Couldn't save that: {}".format(e)
            )
        else:
            self.sc.api_call(
                "chat.postMessage",
                channel=event['channel_id'],
                text="Hrmm... nice pin. I'll have to remember that"
            )


if __name__ == "__main__":
    token = os.environ['SLACK_TOKEN']
    username = 'mrbotserson'
    userid = 'U0PRAMS64'
    bot = MrBoterson(token, username, userid)
    bot.start()
