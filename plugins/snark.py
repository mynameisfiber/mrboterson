from .lib.botplugin import BotPlugin
import random
import time


class SnarkPlugin(BotPlugin):
    queue = []
    probability = 0.1
    messages = [
        "Maybe you should try saying please... I'm not your servant",
        "A 'please' wouldn't kill you?",
        "Do you know how long it's been since I've taken a vacation? " +
            "You could at least say please",
    ]
    waiting_messages = [
        "I'm waiting",
        "I could wait all day for you to respond",
    ]
    thanks = [
        "See! That wasn't hard.",
        "Well... if you put it that way.",
    ]
    come_on = [
        "It's just a couple of letters.",
        "Really? You can't just say please?",
        "I don't even care if you don't mean it... just say please."
    ]

    def events_transform(self, events):
        self.trim_snark()
        for event in events:
            if event['type'] in ('at_mention', 'message') \
                    and event.get('subtype') != 'bot_message':
                for i, q in enumerate(self.queue):
                    if q[1]['user'] == event['user']:
                        if 'please' in event['text_clean']:
                            self.rand_message(event, self.thanks)
                            yield self.queue.pop(i)[1]
                        else:
                            self.rand_message(event, self.come_on)
                        break
                else:
                    if event['type'] == 'at_mention' and \
                            random.random() < self.probability and \
                            'please' not in event['text_clean']:
                        self.queue.append((time.time() + 60, event))
                        self.rand_message(event, self.messages)
                        continue
            yield event

    def trim_snark(self):
        cur_time = time.time()
        while self.queue and self.queue[0][0] < cur_time:
            self.queue = self.queue[1:]
        if self.queue:
            sample = random.choice(self.queue)
            if cur_time - sample[0] > 10:
                self.rand_message(sample[1], self.waiting_messages)

    def rand_message(self, event, messages):
        channel = event['channel']
        who = event['user']
        self.bot.send_message(
            channel,
            "<@{}>: {}".format(who, random.choice(messages))
        )
