from .lib.botplugin import BotPlugin
import itertools as it
import asyncio


class AnimaniacsPlugin(BotPlugin):
    def help(self):
        return {
            "{botname}: something cool": "Does a cool thing",
        }

    async def on_at_mention(self, event):
        message = event['text_clean']
        if 'something cool' in message:
            await self.animation(event)

    async def animation(self, event):
        hearts = it.cycle(":hearts: :green_heart: :blue_heart: :yellow_heart: "
                          ":purple_heart:".split())
        moons = it.cycle(":full_moon: :waning_gibbous_moon: "
                         ":last_quarter_moon: :waning_crescent_moon: "
                         ":new_moon: :waxing_crescent_moon: "
                         ":first_quarter_moon: :moon:".split())
        ret = await self.bot.send_message(event['channel'], 'ok')
        for h, m in it.islice(zip(hearts, moons), 50):
            msg = "{} :cool: :dancer: {}".format(h, m)
            ret = await self.bot.update_message(ret, msg)
            await asyncio.sleep(0.1)
