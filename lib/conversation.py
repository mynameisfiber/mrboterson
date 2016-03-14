import time
from collections import deque


class ConversationManager(object):
    def __init__(self, bot):
        self.queue = deque()
        self.bot = bot

    def start_conversation(self, channel, message, reply_callback=None,
                           users=None, timeout=60, expire_callback=None,
                           meta=None):

        self.bot.send_message(channel, message)
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

    def add_conversation(self, event, reply_callback=None, users=None,
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

    def events_transform(self, events):
        self.trim_queue()
        triggered_conversations = []
        for event in events:
            if self.queue and 'message' in event['type']:
                for i, conv in enumerate(self.queue):
                    if conv.conversation_applies(event):
                        conv.add_event(event)
                        triggered_conversations.append(conv)
            yield_event = True
            if triggered_conversations:
                yield_event = False
                for conv in triggered_conversations:
                    resp = conv.reply_callback(conv)
                    if resp is True:
                        yield_event = True
                triggered_conversations = []
            if yield_event:
                yield event

    def trim_queue(self):
        cur_time = time.time()
        while self.queue and self.queue[0].expire_time < cur_time:
            item = self.queue.popleft()
            if not item.finished and item.expire_callback:
                item.expire_callback(item)


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
