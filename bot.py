from slackclient import SlackClient
import plugins

import os
import traceback
import random
import time
import string
from collections import defaultdict


class MrBoterson(object):
    def __init__(self, token, username, userid, timeout=1):
        self.sc = SlackClient(token)
        self.username = username
        self.userid = userid
        self._at_mention = '<@{}>'.format(userid)
        self.timeout = timeout
        self.plugins = [p(self) for p in plugins.plugins]
        self.events_transforms = [p.events_transform for p in self.plugins]
        self.handlers = defaultdict(list)
        for plugin in self.plugins:
            for event_type, handlers in plugin.handlers.items():
                self.handlers[event_type].extend(handlers)

    def start(self):
        print("Starting bot:", self.username)
        if self.sc.rtm_connect():
            while True:
                try:
                    events = self.sc.rtm_read()
                    self.dispatch_events(events)
                    time.sleep(self.timeout)
                except Exception:
                    print("Exception while handling events: ", events)
                    traceback.print_exc()
        else:
            print("Could not connect to slack")
            return False

    def dispatch_events(self, events):
        events = self.parse_events(events)
        for i, events_transform in enumerate(self.events_transforms):
            events = events_transform(events)
        for event in events:
            event_type = event['type']
            event_handlers = self.handlers.get(event_type, {})
            for handler in event_handlers:
                plugin_name = handler.__self__.__class__.__name__
                print("Dispatching {} to {}".format(event_type, plugin_name))
                handler(event)

    def send_message(self, channel, text):
        return self.sc.api_call("chat.postMessage", channel=channel,
                                text=text, username=self.username,
                                icon_url=self.icon_url)

    @property
    def icon_url(self):
        cat = random.choice(('cats', 'business', 'technics', 'abstract'))
        return 'http://lorempixel.com/48/48/{}?{}'.format(cat, random.random())

    def parse_events(self, events):
        for event in events:
            # messages need some special handling
            if event['type'] == 'message' and 'subtype' in event and \
                    'text' not in event:
                event['type'] = event['subtype']
            if event['type'] == 'message':
                strip = string.punctuation + ' '
                tokens = event['text'].split(' ')
                if tokens[0].startswith("<@U"):
                    event['at_mention'] = tokens[0].strip('@<>:')
                    tokens = tokens[1:]
                # normalize the message
                message = ' '.join(m.lower().strip(strip) for m in tokens)
                event['text_clean'] = message
                if event.get('at_mention', '') == self.userid:
                    event['type'] = 'at_mention'
        return events


if __name__ == "__main__":
    token = os.environ['SLACK_TOKEN']
    username = 'mrbotserson'
    userid = 'U0PRAMS64'
    bot = MrBoterson(token, username, userid)
    bot.start()
