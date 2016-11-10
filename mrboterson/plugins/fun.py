from .lib.botplugin import BotPlugin


class FunPlugin(BotPlugin):
    def help(self):
        return {
            "{botname}: dance": "Do a little dance",
            "{botname}: :bear:": "A meeting of bears",
        }

    async def on_at_mention(self, event):
        message = event['text_clean']
        if message.startswith('dance'):
            await self.bot.send_message(event['channel'], "└[∵┌]└[ ∵ ]┘[┐∵]┘")
        elif message.startswith('bear'):
            await self.bot.send_message(event['channel'],
                                        "http://i.imgur.com/hhxAirt.jpg")
