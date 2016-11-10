from .slack_client import SlackClient, UnexpectedResponseCode
from .conversation import ConversationManager
from .lib.exception_eater import exception_eater_async

import random
import time
import string
from operator import itemgetter
from collections import defaultdict
import asyncio
import logging


class MrBoterson(object):
    def __init__(self, token, userid, plugins=[], timeout=1):
        self.sc = SlackClient(token)
        self.userid = userid
        self.botname = '<@{}>'.format(userid)
        self.timeout = timeout

        self.logger = logging.getLogger(__name__)

        # set up global bot transforms
        self.conversations = ConversationManager(self)
        self.base_event_transforms = [
            self.parse_event,  # should always be first
            self.conversations.event_transform
        ]

        # set up plugins
        self.plugins = [p(self) for p in plugins]
        self.plugin_event_transforms = [p.event_transform
                                        for p in self.plugins]
        self.handlers = defaultdict(list)
        for plugin in self.plugins:
            for event_type, handlers in plugin.handlers.items():
                self.handlers[event_type].extend(handlers)

        self.event_transforms = [*self.base_event_transforms,
                                 *self.plugin_event_transforms]

    async def start(self):
        self.logger.info("Starting bot: %s", self.botname)
        backoff = 1
        while True:
            try:
                self.logger.info("Creating RTM connection")
                await self.sc.real_time_messaging(self.dispatch_event)
            except UnexpectedResponseCode:
                backoff *= 2
                self.logging.error("Could not connect, backing off: " +
                                   "%d seconds", backoff)
                time.sleep(backoff)

    @exception_eater_async
    async def dispatch_event(self, event):
        for event_transform in self.event_transforms:
            event = await event_transform(event)
            if not event:
                return
        event_types = event['type']
        if 'at_mention' in event_types and \
                event['text_clean'].startswith('help'):
            await self.help(event['channel'])
            return
        for event_type in event_types:
            event_handlers = self.handlers.get(event_type, [])
            for handler in event_handlers:
                plugin_name = handler.__self__.__class__.__name__
                self.logger.debug("\nDispatching {} to {}"
                                  .format(event_type, plugin_name))
                asyncio.ensure_future(handler(event))

    async def help(self, channel):
        combined_help = {}
        for plugin in self.plugins:
            combined_help.update(plugin.help())
        output = list(combined_help.items())
        output.sort(key=itemgetter(0))
        help_string = "\n".join("{}\t---\t{}".format(*o) for o in output)
        await self.send_message(channel,
                                help_string.format(botname=self.botname))

    async def send_message(self, channel, text):
        return await self.sc.api_call("chat.postMessage", channel=channel,
                                      text=text, botname=self.botname,
                                      icon_url=self.icon_url, link_names=1)

    async def update_message(self, prev_msg, text):
        ts = prev_msg['ts']
        channel = prev_msg['channel']
        return await self.sc.api_call("chat.update", ts=ts, channel=channel,
                                      text=text, botname=self.botname,
                                      icon_url=self.icon_url, link_names=1)

    async def send_file(self, channel, fd, filename):
        self.logger.debug("Sending file to %s: %s", channel, filename)
        return await self.sc.api_call("files.upload", channels=channel,
                                      filename=filename, file=fd)

    @property
    def icon_url(self):
        cat = random.choice(('cats', 'business', 'technics', 'abstract'))
        return 'http://lorempixel.com/48/48/{}?{}'.format(cat, random.random())

    async def parse_event(self, event):
        if not isinstance(event['type'], set):
            event['type'] = set((event['type'],))
        # messages need some special handling
        if 'subtype' in event:
            event['type'].add(event['subtype'])
            if event['subtype'] in ('message_changed', 'bot_message'):
                event['type'].discard('message')
        if 'message' in event['type'] and 'text' in event:
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
        return event
