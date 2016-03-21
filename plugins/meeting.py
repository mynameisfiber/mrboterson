from .lib.botplugin import BotPlugin
from .lib import text_parser
from dateutil import rrule
from dateutil import parser as dateparser
from datetime import (datetime, timedelta)
import humanize
from collections import defaultdict
from itertools import count
import pickle


def lowest_new_index(keys):
    for i in count(1):
        if i not in keys:
            return i


class MeetingPlugin(BotPlugin):
    def __init__(self, bot):
        try:
            self.db = pickle.load(open("./meeting.pkl"))
        except IOError as e:
            print("Couldn't load meeting backup, starting fresh: ", e)
            self.db = defaultdict(dict)
        super().__init__(bot)

    def _save(self):
        pickle.dump(self.db, open("./meeting.pkl", 'w+'))

    def help(self):
        return {
            "@{botname}: register [every <N>] [day|week|month] [starting <time>]":
                "Registers meetings to happen at the given intervals",
        }

    def on_tick(self, event):
        now = event['datetime']
        before = now - event['dt']
        for channel, meeting in self.db.items():
            if meeting['leadtime'].between(before, now):
                self.nag_leadup(channel, meeting)
            elif meeting['rrule'].between(before, now):
                self.do_meeting(channel, meeting)
                meeting['responses'] = defaultdict(dict)
        return True

    def do_meeting(self, channel, meeting):
        responses = []
        for question, answers in meeting['responses'].items():
            out = 'To the question: {}\n'.format(question) + \
                "\n".join("<@{}> said: {}".format(u, a)
                          for u, a in answers.items())
            responses.append(out)
        self.bot.send_message(channel, "Time for another fun meeting!")
        self.bot.send_message(channel,  "\n".join(responses))

    def do_leadup(self, event):
        meeting_channel = text_parser.get_channels(event['text'])
        if len(meeting_channel) != 1:
            return self.bot.send_message(
                event['channel'],
                "You should tell me what channel this "
                "is for (`start #example`)"
            )
        channel = meeting_channel[0]
        try:
            meeting = self.db[channel]
        except KeyError:
            return self.bot.send_message(event['channel'],
                "Channel isn't registered for meetings")
        questions = list(meeting['questions'].values())
        if not questions:
            return self.bot.send_message(event['channel'],
                "No questions registered for that meeting!")
        meta = {
            'channel': meeting_channel[0],
            'questions': questions[:-1],
            'cur_question': questions[-1],
        }
        self.bot.conversations.start_conversation(
            event['channel'],
            "In one line, tell me: " + meta['cur_question'],
            users=(event['user'],),
            reply_callback=self._on_leadup_response,
            meta=meta,
            timeout=5*60,
            expire_callback=self._try_later
        )

    def _on_leadup_response(self, conv):
        user = conv.users[0]
        meeting_channel = conv.meta['channel']
        meeting = self.db[meeting_channel]
        q_answered = conv.meta['cur_question']
        meeting['responses'][q_answered].setdefault(user, {})
        meeting['responses'][q_answered][user] = \
            conv.events[-1]['text']
        self._save()
        if conv.meta['questions']:
            conv.meta['cur_question'] = conv.meta['questions'].pop()
            self.bot.send_message(conv.channel,
                "In one line, tell me: " + conv.meta['cur_question'])
        else:
            self.bot.send_message(conv.channel,
                                  "OK! You're ready for the meeting")
            conv.done()

    def _try_later(self, conv):
        self.bot.send_message(
            conv.channel,
            "Let's try this again later when you have more time"
        )

    def nag_leadup(self, channel, meeting):
        channel_info = self.bot.sc.api_call('channels.info', channel=channel)
        members = channel_info['channel']['members']
        for member in members:
            dm_info = self.bot.sc.api_call('im.open', user=member)
            if 'error' in dm_info:
                continue
            dm_channel = dm_info['channel']['id']
            self.bot.send_message(
                dm_channel,
                ("Ready to start pre-meeting for <#{0}>? "
                 "Just say 'start <#{0}>' to begin!").format(channel)
            )

    def on_at_mention(self, event):
        if event['text_clean'].startswith('register'):
            try:
                repeat, leadtime, repeat_str = _parse_rrule(event)
            except Exception as e:
                self.bot.send_message(event['channel'],
                                      "Can't parse date: " + str(e))
            else:
                meeting = {'rrule': repeat, 'leadtime': leadtime,
                           'questions': {}, 'responses': defaultdict(dict)}
                self.db[event['channel']] = meeting
                self.bot.send_message(
                    event['channel'],
                    "Channel <#{}> registered for meetings {}".format(
                        event['channel'],
                        repeat_str
                    )
                )
                self._save()
        elif event['text_clean'].startswith('unregister'):
            removed = self.db.pop(event['channel'], None)
            if removed:
                self.bot.send_message(event['channel'],
                                      "Channel was never registered!")
            else:
                self.bot.send_message(
                    event['channel'],
                    "No more meetings in <#{}>! Woo!".format(event['channel'])
                )
                self._save()
        elif event['text_clean'].startswith('list questions'):
            questions = ", ".join(
                '"[{}] {}"'.format(i, q)
                for i, q in self.db[event['channel']]['questions'].items()
            )
            self.bot.send_message(
                event['channel'],
                "Questions registered on this channel: " + questions
            )
        elif event['text_clean'].startswith('add question'):
            if event['channel'] not in self.db:
                self.bot.send_message(event['channel'],
                                      "Channel not registered")
            else:
                channel_qs = self.db[event['channel']]['questions']
                idx = lowest_new_index(channel_qs)
                question = event['text_clean'][len('add question'):] + '?'
                channel_qs[idx] = question.strip()
                self.bot.send_message(event['channel'],
                                      "Added new question: " + question)
                self._save()
        elif event['text_clean'].startswith('delete question'):
            message = event['text_clean']
            qids = [int(m) for m in message.split(' ') if m.isnumeric()]
            if event['channel'] not in self.db:
                self.bot.send_message(event['channel'],
                                      "Channel not registered")
            elif any(q not in self.db[event['channel']]['questions']
                     for q in qids):
                self.bot.send_message(event['channel'],
                                      "Question ID not in use")
            else:
                channel_qs = self.db[event['channel']]['questions']
                responses = self.db[event['channel']]['responses']
                removed_questions = (channel_qs.pop(qid) for qid in qids)
                for qid in qids:
                    responses.pop(qid, None)
                removed_notification = ", ".join('"{}"'.format(q)
                                                 for q in removed_questions)
                self.bot.send_message(event['channel'],
                                      "Removed: " + removed_notification)
                self._save()
        elif event['text_clean'].startswith('show answers'):
            possible_channel = text_parser.get_channels(event['text'])
            if possible_channel:
                channel = possible_channel[0]
            else:
                channel = event['channel']
            try:
                meeting = self.db[channel]
            except KeyError:
                return self.bot.send_message(channel,
                    "Channel doesn't have any meetings")
            self.do_meeting(event['channel'], meeting)
        else:
            return False
        return True

    def on_direct_message(self, event):
        if event['channel'][0] == 'D' and \
                event['text_clean'].startswith('start'):
            self.do_leadup(event)
            return True
        return False


def _parse_rrule(event):
    message = event['text_clean']
    freq = None
    if 'week' in message:
        freq = rrule.WEEKLY
        leadtime = timedelta(days=1)
        freq_str = "week"
    elif 'month' in message:
        freq = rrule.MONTHLY
        leadtime = timedelta(weeks=1)
        freq_str = "month"
    elif 'day' in message or 'daily' in message:
        freq = rrule.DAILY
        leadtime = timedelta(hours=1)
        freq_str = "day"
    elif 'minute' in message:
        freq = rrule.MINUTELY
        leadtime = timedelta(seconds=1)
        freq_str = "minute"
    else:
        return None
    tokens = message.split()
    try:
        interval_idx = tokens.index('every')
        interval = int(tokens[interval_idx+1])
    except ValueError:
        interval = 1
    try:
        start_idx = tokens.index('starting')
        dtstart = dateparser.parse(" ".join(tokens[start_idx+1:]), fuzzy=True)
    except ValueError as e:
        dtstart = datetime.now()

    human_str = "every {} {} starting in {}".format(
        interval,
        freq_str + ('s' if interval > 0 else ''),
        humanize.naturaltime(datetime.now() - dtstart, future=True)
    )
    repeat_rule = rrule.rrule(freq, dtstart=dtstart, interval=interval)
    leadtime_rule = rrule.rrule(freq, dtstart=dtstart-leadtime, interval=interval)
    return repeat_rule, leadtime_rule, human_str
