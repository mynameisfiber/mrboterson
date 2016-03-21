from slackclient import SlackClient
from websocket._exceptions import WebSocketConnectionClosedException
from lib.conversation import ConversationManager
import plugins

import os
import traceback
import random
import time
from datetime import (timedelta, datetime)
import string
from operator import itemgetter
from collections import defaultdict


class MrBoterson(object):
    def __init__(self, token, botname, userid, timeout=1):
        self.sc = SlackClient(token)
        self.botname = botname
        self.userid = userid
        self._at_mention = '<@{}>'.format(userid)
        self.timeout = timeout
        self.injected_events = []

        # set up global bot transforms
        self.conversations = ConversationManager(self)
        self.events_transforms = [
            self.parse_events, # should always be first
            self.conversations.events_transform
        ]

        # set up plugins
        self.plugins = [p(self) for p in plugins.plugins]
        self.plugin_events_transforms = [p.events_transform
                                         for p in self.plugins]
        self.handlers = defaultdict(list)
        for plugin in self.plugins:
            for event_type, handlers in plugin.handlers.items():
                self.handlers[event_type].extend(handlers)

    def start(self):
        print("Starting bot:", self.botname)
        backoff = 1
        if not self.sc.rtm_connect():
            print("Could not connect to slack")
            return False
        while True:
            try:
                events = self.sc.rtm_read()
                self.dispatch_events(events)
                time.sleep(self.timeout)
            except WebSocketConnectionClosedException:
                print("Websocket disconnected... attempting reconnect")
                if not self.sc.rtm_connect():
                    print("Could not connect, backing off: " +
                          "{} seconds".format(backoff))
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    print("Reconnected!")
                    backoff = 1
            except Exception:
                print("Exception while handling events: ", events)
                traceback.print_exc()

    def inject_event(self, event):
        self.injected_events.append(event)

    def dispatch_events(self, events):
        tick_event = [{'type': 'tick', 't': time.time(),
                       'datetime': datetime.now(),
                       'dt': timedelta(seconds=self.timeout)}]
        events = self.injected_events + tick_event + events
        self.injected_events = self.injected_events[:0]
        for events_transform in self.events_transforms:
            events = events_transform(events)
        for events_transform in self.plugin_events_transforms:
            events = events_transform(events)
        for event in events:
            did_respond = None
            event_types = event['type']
            if 'at_mention' in event_types and \
                    event['text_clean'].startswith('help'):
                self.help(event['channel'])
                did_respond = True
                continue
            for event_type in event_types:
                event_handlers = self.handlers.get(event_type, [])
                for handler in event_handlers:
                    plugin_name = handler.__self__.__class__.__name__
                    if 'tick' in event_type:
                        print('.', end='', flush=True)
                    else:
                        print("\nDispatching {} to {}"
                              .format(event_type, plugin_name), end='')
                    response = handler(event)
                    if response is not None and response:
                        did_respond = True
            if did_respond is not None and not did_respond and \
                    event_type not in ('tick', 'message'):
                self.send_message(event['channel'], "whhaaa?")

    def help(self, channel):
        combined_help = {}
        for plugin in self.plugins:
            combined_help.update(plugin.help())
        output = list(combined_help.items())
        output.sort(key=itemgetter(0))
        help_string = "\n".join("{}\t---\t{}".format(*o) for o in output)
        self.send_message(channel, help_string.format(botname=botname))

    def send_message(self, channel, text):
        return self.sc.api_call("chat.postMessage", channel=channel,
                                text=text, botname=self.botname,
                                icon_url=self.icon_url, link_names=1)

    @property
    def icon_url(self):
        cat = random.choice(('cats', 'business', 'technics', 'abstract'))
        return 'http://lorempixel.com/48/48/{}?{}'.format(cat, random.random())

    def parse_events(self, events):
        for event in events:
            if not isinstance(event['type'], set):
                event['type'] = set((event['type'],))
            # messages need some special handling
            if 'subtype' in event:
                event['type'].add(event['subtype'])
                if event['subtype'] in ('message_changed', 'bot_message'):
                    event['type'].discard('message')
            if 'message' in event['type']:
                strip = string.punctuation + ' '
                tokens = event['text'].split(' ')
                if tokens[0].startswith("<@U"):
                    event['at_mention'] = tokens[0].strip('@<>:')
                    tokens = tokens[1:]
                # normalize the message
                message = ' '.join(m.lower().strip(strip) for m in tokens)
                event['text_clean'] = message
                if event.get('at_mention', '') == self.userid:
                    event['type'].add('at_mention')
                if event.get('channel', '').startswith("D"):
                    event['type'].add('direct_message')
            yield event


if __name__ == "__main__":
    token = os.environ['SLACK_TOKEN']
    botname = 'mrboterson'
    userid = 'U0SJU20P7'
    bot = MrBoterson(token, botname, userid)
    bot.start()
