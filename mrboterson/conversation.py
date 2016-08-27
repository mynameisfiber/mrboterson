import time
from collections import deque
import asyncio


class ConversationManager(object):
    def __init__(self, bot):
        self.queue = deque()
        self.bot = bot
        asyncio.ensure_future(self.trim_queue())

    async def start_conversation(self, channel, message, reply_callback=None,
                                 users=None, timeout=60, expire_callback=None,
                                 meta=None):

        await self.bot.send_message(channel, message)
        conv = Conversation(
            reply_callback=reply_callback,
            users=users,
            channel=channel,
            timeout=timeout,
            expire_callback=expire_callback,
            meta=meta
        )
        self.queue.append(conv)
        return conv

    async def add_conversation(self, event, reply_callback=None, users=None,
                               channel=None, timeout=60, expire_callback=None,
                               meta=None):
        conv = Conversation(
            event=event,
            reply_callback=reply_callback,
            users=users,
            channel=channel,
            timeout=timeout,
            expire_callback=expire_callback,
            meta=meta
        )
        self.queue.append(conv)
        return conv

    async def event_transform(self, event):
        triggered_conversations = []
        if self.queue and 'message' in event['type']:
            for i, conv in enumerate(self.queue):
                if conv.conversation_applies(event):
                    conv.add_event(event)
                    triggered_conversations.append(conv)
        if not triggered_conversations:
            return event
        return_event = False
        for conv in triggered_conversations:
            return_event |= bool(await conv.reply_callback(conv))
        if return_event:
            return event

    async def trim_queue(self):
        timeout = self.bot.timeout
        while True:
            cur_time = time.time()
            while self.queue and self.queue[0].expire_time < cur_time:
                item = self.queue.popleft()
                if not item.finished and item.expire_callback:
                    await item.expire_callback(item)
            await asyncio.sleep(timeout)


class Conversation(object):
    def __init__(self, event=None, users=None, channel=None,
                 reply_callback=None, expire_callback=None,
                 meta=None, timeout=60):
        assert users is not None or channel is not None
        self.events = [] if event is None else [event]
        self.reply_callback = reply_callback
        self.expire_callback = expire_callback
        self.users = users
        self.channel = channel
        self.expire_time = time.time() + timeout
        self.meta = meta
        self.finished = False

    def add_event(self, event):
        self.events.append(event)

    def conversation_applies(self, event):
        return (not self.finished and
                (self.users is None or event.get('user') in self.users) and
                (self.channel is None or self.channel == event.get('channel')))

    def done(self):
        self.finished = True
