from .lib.botplugin import BotPlugin
import requests
from fuzzywuzzy import fuzz
from operator import itemgetter
from collections import Counter


class TriviaPlugin(BotPlugin):
    status = {}

    def help(self):
        return {
            "@{botname}: start trivia": "Starts trivia",
            "@{botname}: stop trivia": "Where once there was trivia, there will no longer be",
            "@{botname}: score": "Where once there was trivia, tells you the score",
        }

    def on_at_mention(self, event):
        channel = event['channel']
        message = event['text_clean']
        if message.startswith('start trivia'):
            self._start_trivia(channel)
            return True
        elif channel in self.status:
            if event['text_clean'].startswith('score'):
                scores = self.status[channel]['scores']
                self.show_scores(channel, scores)
                return True
            elif event['text_clean'].startswith('stop trivia'):
                self._end_trivia(channel)
                return True
        return False

    def _start_trivia(self, channel):
        if channel in self.status:
            return self.bot.send_message(channel,
                "Already running trivia! Pay attention")
        self.status[channel] = {'conv': None, 'scores': Counter()}
        self.ask_question(channel)

    def _end_trivia(self, channel):
        if channel not in self.status:
            return self.bot.send_message(channel,
                "Not running trivia! Pay attention")
        conv = self.status[channel]['conv']
        if conv is not None:
            conv.done()
        data = self.status.pop(channel)
        self.bot.send_message(channel, 'Trivia over!')
        self.show_scores(channel, data['scores'])

    def show_scores(self, channel, scores):
        scores = list(scores.items())
        scores.sort(reverse=True, key=itemgetter(1))
        scores_str = "\n".join("<@{}> got {} points".format(u, s)
                               for u, s in scores)
        scores_str = scores_str or 'No points yet!'
        self.bot.send_message(channel, "Scoreboard:")
        self.bot.send_message(channel, scores_str)

    def ask_question(self, channel):
        if channel not in self.status:
            return
        if self.status[channel]['scores']:
            self.show_scores(channel, self.status[channel]['scores'])
        try:
            q = None
            while q is None:
                question = requests.get("http://jservice.io/api/random").json()[0]
                q = question['question']
        except Exception as e:
            self.bot.send_message(channel,
                "Couldn't get trivia questions... try again later: " + str(e))
            self._end_trivia(channel)
        meta = question
        meta['attempts'] = 0
        meta['value'] = meta['value'] or 100
        conv = self.bot.conversations.start_conversation(
            channel,
            'The category is {q[category][title]} for {q[value]}: {q[question]}'.format(q=question),
            reply_callback=self._on_answer,
            expire_callback=self._end_time,
            timeout=45,
            meta=meta,
        )
        self.status[channel]['conv'] = conv

    def _on_answer(self, conv):
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
                    self.bot.send_message(channel,
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
            self.bot.send_message(channel,
                "<@{}> got it right! The answer was {}".format(user, answer))
            conv.done()
            self.ask_question(channel)
        return True

    def _end_time(self, conv):
        channel = conv.channel
        answer = conv.meta['answer']
        self.bot.send_message(channel,
            "Nobody got it... the answer is {}".format(answer))
        conv.done()
        if conv.meta['attempts']:
            self.ask_question(channel)
        else:
            self.bot.send_message(channel,
                "Turning off trivia until you get your head in the game")

