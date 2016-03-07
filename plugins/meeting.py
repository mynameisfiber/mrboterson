from .lib.botplugin import BotPlugin
from dateutil import rrule
from dateutil import parser as dateparser
from datetime import (datetime, timedelta)
from collections import defaultdict
from itertools import count
import humanize


def lowest_new_index(keys):
    for i in count(1):
        if i not in keys:
            return i


class MeetingPlugin(BotPlugin):
    db = defaultdict(dict)

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
        return True

    def do_meeting(self, channel, meeting):
        responses = []
        for question, responses in meeting['responses']:
            out = 'To the question: {}\n'.format(question) + \
                "\n".join("<@{}> said: {}".format(u, r)
                          for u, r in responses.items())
            responses.append(out)
        self.bot.message(channel, "Time for another fun meeting!")
        self.bot.message(channel,  "\n".join(responses))

    def do_leadup(self, event):
        # TODO: extract channel id from message and start the
        # _on_leadup_response process.. still need to figure out the format of
        # the `responses` key
        pass

    def _on_leadup_response(self, conv):
        meeting_channel = conv.meta['channel']
        meeting = self.db[meeting_channel]
        q_answered = conv.meta['qid_queue'].pop()
        meeting['responses'][q_answered][conv.user] = conv.events[-1]['text']
        if conv.meta['qid_queue']:
            qid = conv.meta['qid_queue'][-1]
            self.bot.conversations.start_converation(
                meeting['questions'][qid],
                user=conv.user,
                channel=conv.channel,
                reply_callback=self._on_leadup_response,
                expire_callback=self._try_later,
                timeout=60*10,
            )

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
                question = event['text_clean'][len('add question'):]
                channel_qs[idx] = question
                self.bot.send_message(event['channel'],
                                      "Added new question: " + question)
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
        elif event['channel'][0] == 'D' and \
                event['text_clean'].startswith('start'):
            self.do_leadup(event)
        else:
            return False
        return True


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
        print(e)
        dtstart = datetime.now()

    human_str = "every {} {} starting in {}".format(
        interval,
        freq_str + ('s' if interval > 0 else ''),
        humanize.naturaltime(datetime.now() - dtstart, future=True)
    )
    repeat_rule = rrule.rrule(freq, dtstart=dtstart, interval=interval)
    leadtime_rule = rrule.rrule(freq, dtstart=dtstart-leadtime, interval=interval)
    return repeat_rule, leadtime_rule, human_str
