from .lib.botplugin import BotPlugin
from .lib.pindb import (PinDB, format_pin)


class PinsPlugin(BotPlugin):
    def __init__(self, bot):
        self.pindb = PinDB("./pindb.sql")
        super().__init__(bot)

    def help(self):
        return {
            "@{botname}: get pins": "Show pins",
            "@{botname}: pin [N]": "Pin the last N messages",
            "@{botname}: delete pin [ID]": "Delete pin with ID",
        }

    async def on_at_mention(self, event):
        message = event['text_clean']
        if message.startswith('get pins'):
            channel = event['channel']
            for pin in self.pindb.get_pins(channel=channel):
                await self.bot.send_message(event['channel'], format_pin(pin))
        elif message.startswith('pin'):
            numbers = [int(m) for m in message.split(' ') if m.isnumeric()]
            if len(numbers) > 1:
                return await self.bot.send_message(event['channel'],
                                                   "errr... I didn't get that")
            count = 1
            if numbers:
                count = numbers[0]
            history = self.bot.sc.api_call(
                'channels.history',
                channel=event['channel'],
                latest=event['ts'],
                count=count
            )
            await self._save_pin(history['messages'], meta=event)
        elif message.startswith('delete pin'):
            pins = [int(m) for m in message.split(' ') if m.isnumeric()]
            for pin_id in pins:
                self.pindb.delete_pin(pin_id)
            await self.bot.send_message(event['channel'], "Deleted pins")

    async def on_pinned_item(self, event):
        if 'attachments' in event:
            await self._save_pin(event['attachments'], meta=event)
        elif 'item' in event:
            event['item']['text'] = event['text']
            await self._save_pin((event['item'],), meta=event)
        else:
            await self.bot.send_message(
                event['channel'],
                "I don't understand that type of pin. is it like... " +
                "meta or something?"
            )
        return True

    async def on_pin_remove(self, event):
        return False

    async def _save_pin(self, pins, meta):
        try:
            self.pindb.save_pins(pins, meta)
        except Exception as e:
            await self.bot.send_message(
                meta['channel'],
                "Couldn't save that: {}".format(e)
            )
        else:
            await self.bot.send_message(
                meta['channel'],
                "Hrmm... nice pin. I'll have to remember that"
            )
