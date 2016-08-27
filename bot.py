import os
import asyncio

from mrboterson import MrBoterson
from plugins import plugins


if __name__ == "__main__":
    token = os.environ['SLACK_TOKEN']
    userid = os.environ['SLACK_ID']
    bot = MrBoterson(token, userid, plugins=plugins)
    future = bot.start()

    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(future)
    loop.close()
