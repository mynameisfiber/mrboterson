from slackclient import SlackClient
import plugins

import os
import time
import string
from collections import (defaultdict, deque)


class MrBoterson(object):
    def __init__(self, token, username, userid, timeout=1, history=1000):
        self.sc = SlackClient(token)
        self.username = username
        self.userid = userid
        self._at_mention = '<@{}>'.format(userid)
        self.timeout = timeout
        self._history = defaultdict(lambda: deque(maxlen=history))
        self.plugins = [p(self) for p in plugins.plugins]
        self.handlers = defaultdict(list)
        for plugin in self.plugins:
            for event_type, handlers in plugin.handlers.items():
                self.handlers[event_type].extend(handlers)

    def start(self):
        print("Starting bot:", self.username)
        if self.sc.rtm_connect():
            while True:
                events = self.sc.rtm_read()
                self.dispatch_events(events)
                time.sleep(self.timeout)
        return False

    def dispatch_events(self, events):
        for event in events:
            event_type = event['type']
            # first we take care of special handlers
            if event_type == 'message':
                strip = string.punctuation + ' '
                message = event['text'][len(self._at_mention):] \
                    .strip(strip)
                # normalize the message
                message = ' '.join(m.strip(strip) for m in message.split(' '))
                event['text_clean'] = message
                # add to history
                self._history[event['channel']].append(event)
                if event.get('text', '').startswith(self._at_mention):
                    event_type = 'at_mention'
            event_handlers = self.handlers.get(event_type, {})
            for handler in event_handlers:
                plugin_name = handler.__self__.__class__.__name__
                print("Dispatching {} to {}".format(event_type, plugin_name))
                handler(event)

    def send_message(self, channel, text):
        return self.sc.api_call("chat.postMessage", channel=channel,
                                text=text, username=self.username)


if __name__ == "__main__":
    token = os.environ['SLACK_TOKEN']
    username = 'mrbotserson'
    userid = 'U0PRAMS64'
    bot = MrBoterson(token, username, userid)
    bot.start()
