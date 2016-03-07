from .lib.botplugin import BotPlugin


class FunPlugin(BotPlugin):
    def help(self):
        return {
            "@{botname}: dance": "Do a little dance",
        }

    def on_at_mention(self, event):
        message = event['text_clean']
        if message.startswith('dance'):
            self.bot.send_message(event['channel'], "└[∵┌]└[ ∵ ]┘[┐∵]┘")
            return True
        return False
