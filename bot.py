from slackclient import SlackClient
from pindb import PinDB

import os
import time
import string


def format_pin(pin):
    return ("On {pin_timestamp:%Y-%m-%d %H:%M:%S} " +
            "<@{pin_user}> pinned: " +
            "<@{msg_user}> : {message}").format(**pin)


class MrBoterson(object):
    def __init__(self, token, username, userid, timeout=1):
        self.sc = SlackClient(token)
        self.username = username
        self.userid = userid
        self._at_mention = '<@{}>'.format(userid)
        self.timeout = timeout
        self.pindb = PinDB("./pindb.sql")

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
            for pin in self.pindb.get_pins(channel):
                self.sc.api_call("chat.postMessage", channel=event['channel'],
                                 text=format_pin(pin), username=username)
        else:
            self.sc.api_call("chat.postMessage", channel=event['channel'],
                             text="stop taking to me", username=username)

    def on_pin(self, event):
        if event['item']['type'] != 'message':
            self.sc.api_call(
                "chat.postMessage",
                channel=event['channel_id'],
                text="How insensitive... I only save text pins."
            )
        try:
            self.pindb.save_pin(event)
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
