from slackclient import SlackClient

import time
import os
import string


class MrBoterson(object):
    def __init__(self, token, username, userid, timeout=1):
        self.sc = SlackClient(token)
        self.username = username
        self.userid = userid
        self._at_mention = '<@{}>'.format(userid)
        self.timeout = timeout

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
        message = event['text'][self._at_mention:] \
            .strip(strip)
        tokens = [m.strip(strip) for m inmessage.split(' ')]
        if tokens[0] == 'dance':
            self.sc.api_call("chat.postMessage", channel=event['channel'],
                             text="└[∵┌]└[ ∵ ]┘[┐∵]┘", username=username)
        else:
            self.sc.api_call("chat.postMessage", channel=event['channel'],
                             text="stop taking to me", username=username)

    def on_pin(self, event):
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
