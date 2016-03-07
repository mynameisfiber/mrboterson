from .lib.botplugin import BotPlugin
import random


class SnarkPlugin(BotPlugin):
    probability = 0.05
    messages = [
        "Maybe you should try saying please... I'm not your servant",
        "A 'please' wouldn't kill you.",
        "Do you know how long it's been since I've taken a vacation?",
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
    give_up = [
        "Fine... I hate you too.",
    ]

    def events_transform(self, events):
        for event in events:
            if event['type'] == 'at_mention' and \
                    'ignore_snark' not in event and \
                    random.random() < self.probability and \
                    'please' not in event['text_clean']:
                conv = self.bot.conversations.add_conversation(
                    event,
                    reply_callback=self.reply_callback,
                    expire_callback=self.expire_callback,
                )
                self.rand_message(conv, self.messages)
            else:
                yield event

    def reply_callback(self, conv):
        if 'please' in conv.events[-1]['text_clean']:
            self.rand_message(conv, self.thanks)
            orig_event = conv.events[0]
            orig_event['ignore_snark'] = True
            self.bot.inject_event(orig_event)
            conv.done()
        else:
            self.rand_message(conv, self.come_on)

    def expire_callback(self, conv):
        self.rand_message(conv, self.give_up)

    def rand_message(self, conv, messages):
        channel = conv.channel
        who = " ".join("<@{}>:".format(w) for w in conv.users)
        self.bot.send_message(
            channel,
            "{} {}".format(who, random.choice(messages))
        )
