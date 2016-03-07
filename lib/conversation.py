import time
from collections import deque


class ConversationManager(object):
    def __init__(self):
        self.queue = deque()

    def add_conversation(self, event, reply_callback, users=None, channel=None,
                         timeout=60, expire_callback=None, meta=None):
        conv = Conversation(
            event,
            reply_callback,
            users,
            channel,
            timeout,
            expire_callback,
            meta
        )
        self.queue.append(conv)
        return conv

    def events_transform(self, events):
        self.trim_queue()
        triggered_conversations = []
        for event in events:
            if event['type'] in ('at_mention', 'message'):
                for i, conv in enumerate(self.queue):
                    if conv.conversation_applies(event):
                        conv.add_event(event)
                        triggered_conversations.append(conv)
            if triggered_conversations:
                for conv in triggered_conversations:
                    conv.reply_callback(conv)
                triggered_conversations = []
            else:
                yield event

    def trim_queue(self):
        cur_time = time.time()
        while self.queue and self.queue[0].expire_time < cur_time:
            item = self.queue.popleft()
            if item.expire_callback:
                item.expire_callback(item)


class Conversation(object):
    def __init__(self, event, reply_callback, users=None, channel=None,
                 timeout=60, expire_callback=None, meta=None):
        self.events = [event]
        self.reply_callback = reply_callback
        self.expire_callback = expire_callback
        self.users = users or (event['user'],)
        self.channel = channel or event['channel']
        self.expire_time = time.time() + timeout
        self.meta = meta
        self.finished = False

    def add_event(self, event):
        self.events.append(event)

    def conversation_applies(self, event):
        return (not self.finished and event['user'] in self.users and
                self.channel == event['channel'])

    def done(self):
        self.finished = True
