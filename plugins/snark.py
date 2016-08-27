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

    async def event_transform(self, event):
        if 'at_mention' in event['type']:
            if event['text_clean'].startswith('please'):
                event['text_clean'] = event['text_clean'][6:].strip()
            elif event['text_clean'].endswith('please'):
                event['text_clean'] = event['text_clean'][:-6].strip()
            elif 'ignore_snark' not in event and \
                    random.random() < self.probability:
                conv = await self.bot.conversations.add_conversation(
                    event,
                    users=(event['user'],),
                    channel=event['channel'],
                    reply_callback=self.reply_callback,
                    expire_callback=self.expire_callback,
                )
                await self.rand_message(conv, self.messages)
                return
        return event

    async def reply_callback(self, conv):
        if 'please' in conv.events[-1]['text_clean']:
            conv.done()
            await self.rand_message(conv, self.thanks)
            orig_event = conv.events[0]
            orig_event['ignore_snark'] = True
            await self.bot.dispatch_event(orig_event)
        else:
            await self.rand_message(conv, self.come_on)

    async def expire_callback(self, conv):
        await self.rand_message(conv, self.give_up)

    async def rand_message(self, conv, messages):
        channel = conv.channel
        who = " ".join("<@{}>:".format(w) for w in conv.users)
        await self.bot.send_message(
            channel,
            "{} {}".format(who, random.choice(messages))
        )
