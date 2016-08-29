from .lib.botplugin import BotPlugin
import aiohttp
import os


class SummarizePlugin(BotPlugin):
    url = os.environ.get('SUMMARY_URL', '')
    username = os.environ.get('SUMMARY_USER', '')
    password = os.environ.get('SUMMARY_PASSWORD', '')

    def help(self):
        return {
            "{botname}: summarize": "Summarize the channel",
        }

    async def on_at_mention(self, event):
        message = event['text_clean']
        if message.startswith('summarize'):
            await self.summarize(event['channel'])

    async def summarize(self, channel):
        status = await self.bot.send_message(channel,
                                             "Alright... getting the history")
        history = await self.bot.sc.api_call(
            'channels.history',
            channel=channel,
            count=500,
        )
        messages = [m['text'] for m in history['messages']]
        status = await self.bot.update_message(status,
                                               "Summarizing... beep beep... "
                                               "bloop bloop")
        try:
            best_sentences = await self._fetch_summary(messages)
        except:
            return await self.bot.update_message(status,
                                                 "couldn't get a summary")
        summary = "A couple particularly good sentences from the " + \
                  "past little bit:\n"
        summary += "\n".join("\t{sent} [{score:0.2f}]".format(**s)
                             for s in best_sentences)
        await self.bot.update_message(status, summary)

    async def _fetch_summary(self, messages):
        response = await aiohttp.post(self.url, data="\n".join(messages), auth=auth)
        result = await response.json()

        return result['scored_article_sentences'][:5]
