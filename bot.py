import os
import asyncio
import logging

from mrboterson import MrBoterson
from mrboterson.plugins import plugins


FORMAT = ('[%(asctime)-15s][%(levelname)s][%(module)s.%(funcName)s:%(lineno)d]'
          '%(message)s')
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.DEBUG)


if __name__ == "__main__":
    token = os.environ['SLACK_TOKEN']
    userid = os.environ['SLACK_ID']
    bot = MrBoterson(token, userid, plugins=plugins)
    future = bot.start()

    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(future)
    loop.close()
