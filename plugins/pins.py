from .lib.botplugin import BotPlugin
from .lib.pindb import (PinDB, format_pin)


class PinsPlugin(BotPlugin):
    def __init__(self, bot):
        self.pindb = PinDB("./pindb.sql")
        super().__init__(bot)

    def on_at_mention(self, event):
        message = event['text_clean']
        if message.startswith('dance'):
            self.bot.send_message(event['channel'], "└[∵┌]└[ ∵ ]┘[┐∵]┘")
        elif message.startswith('get pin'):
            channel = event['channel']
            for pin in self.pindb.get_pins(channel):
                self.bot.send_message(event['channel'], format_pin(pin))
        elif message.startswith('delete pin'):
            pins = [int(m) for m in message.split(' ') if m.isnumeric()]
            for pin_id in pins:
                self.pindb.delete_pin(pin_id)
            self.bot.send_message(event['channel'], "Deleted pins")
        else:
            self.bot.send_message(event['channel'], "stop taking to me")

    def on_pin(self, event):
        if event['item']['type'] != 'message':
            self.bot.send_message(
                event['channel_id'],
                "How insensitive... I only save _text_ pins."
            )
        try:
            self.pindb.save_pin(event)
        except Exception as e:
            self.bot.send_message(
                event['channel_id'],
                "Couldn't save that: {}".format(e)
            )
        else:
            self.bot.send_message(
                event['channel_id'],
                "Hrmm... nice pin. I'll have to remember that"
            )

    def on_pin_remove(self, event):
        pass
