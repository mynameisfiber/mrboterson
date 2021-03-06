from .lib.botplugin import BotPlugin
from fuzzywuzzy import fuzz
from operator import itemgetter
from collections import Counter
import aiohttp


class TriviaPlugin(BotPlugin):
    status = {}

    def help(self):
        return {
            "{botname}: start trivia": "Starts trivia",
            "{botname}: stop trivia": "Where once there was trivia, there will no longer be",
            "{botname}: score": "Where once there was trivia, tells you the score",
        }

    async def on_at_mention(self, event):
        channel = event['channel']
        message = event['text_clean']
        if message.startswith('start trivia'):
            await self._start_trivia(channel)
        elif channel in self.status:
            if event['text_clean'].startswith('score'):
                scores = self.status[channel]['scores']
                await self.show_scores(channel, scores)
            elif event['text_clean'].startswith('stop trivia'):
                await self._end_trivia(channel)

    async def _start_trivia(self, channel):
        if channel in self.status:
            return await self.bot.send_message(channel,
                "Already running trivia! Pay attention")
        self.status[channel] = {'conv': None, 'scores': Counter()}
        await self.ask_question(channel)

    async def _end_trivia(self, channel):
        if channel not in self.status:
            return await self.bot.send_message(channel,
                "Not running trivia! Pay attention")
        conv = self.status[channel]['conv']
        if conv is not None:
            conv.done()
        data = self.status.pop(channel)
        await self.bot.send_message(channel, 'Trivia over!')
        await self.show_scores(channel, data['scores'])

    async def show_scores(self, channel, scores):
        scores = list(scores.items())
        scores.sort(reverse=True, key=itemgetter(1))
        scores_str = "\n".join("<@{}> got {} points".format(u, s)
                               for u, s in scores)
        scores_str = scores_str or 'No points yet!'
        await self.bot.send_message(channel, "Scoreboard:")
        await self.bot.send_message(channel, scores_str)

    async def ask_question(self, channel):
        if channel not in self.status:
            return
        if self.status[channel]['scores']:
            await self.show_scores(channel, self.status[channel]['scores'])
        try:
            question = await self.get_question()
        except Exception as e:
            await self.bot.send_message(channel,
                "Couldn't get trivia questions... try again later: " + str(e))
            await self._end_trivia(channel)
            return
        meta = question
        meta['attempts'] = 0
        meta['value'] = meta['value'] or 100
        conv = await self.bot.conversations.start_conversation(
            channel,
            'The category is {q[category][title]} for {q[value]}: {q[question]}'.format(q=question),
            reply_callback=self._on_answer,
            expire_callback=self._end_time,
            timeout=45,
            meta=meta,
        )
        self.status[channel]['conv'] = conv

    async def get_question(self):
        url = "http://jservice.io/api/random"
        with aiohttp.ClientSession() as session:
            q = None
            while q is None:
                async with session.get(url) as resp:
                    question = (await resp.json())[0]
                    q = question['question']
            return question

    async def _on_answer(self, conv):
        channel = conv.channel
        answer = conv.meta['answer'].lower()
        win_event = None
        for event in conv.events:
            if 'trivia' in event:
                continue
            score = fuzz.token_set_ratio(event['text_clean'], answer)
            if score > 80:
                win_event = event
                break
            elif score > 50:
                try:
                    await self.bot.send_message(channel,
                        "<@{}> Not quite...".format(event['user']))
                except KeyError as e:
                    import traceback
                    print("\n\nSomething went wrong in trivia")
                    traceback.print_exc()
            event['trivia'] = True
            conv.meta['attempts'] += 1
        if win_event is not None:
            user = win_event['user']
            self.status[channel]['scores'][user] += conv.meta['value']
            await self.bot.send_message(channel,
                "<@{}> got it right! The answer was {}".format(user, answer))
            conv.done()
            await self.ask_question(channel)
        return True

    async def _end_time(self, conv):
        channel = conv.channel
        answer = conv.meta['answer']
        await self.bot.send_message(channel,
            "Nobody got it... the answer is {}".format(answer))
        conv.done()
        if conv.meta['attempts']:
            await self.ask_question(channel)
        else:
            await self.bot.send_message(channel,
                "Turning off trivia until you get your head in the game")

