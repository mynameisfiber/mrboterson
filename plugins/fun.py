from .lib.botplugin import BotPlugin


class FunPlugin(BotPlugin):
    def help(self):
        return {
            "@{botname}: dance": "Do a little dance",
            "@{botname}: :bear:": "A meeting of bears",
        }

    def on_at_mention(self, event):
        message = event['text_clean']
        if message.startswith('dance'):
            self.bot.send_message(event['channel'], "└[∵┌]└[ ∵ ]┘[┐∵]┘")
            return True
        elif message.startswith('bear'):
            self.bot.send_message(event['channel'], 
                                  "http://i.imgur.com/hhxAirt.jpg")
            return True
        return False
