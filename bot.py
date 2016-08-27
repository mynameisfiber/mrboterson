import os

from mrboterson import MrBoterson
from plugins import plugins


if __name__ == "__main__":
    token = os.environ['SLACK_TOKEN']
    userid = os.environ['SLACK_ID']
    botname = 'mrboterson'
    bot = MrBoterson(token, botname, userid, plugins=plugins)
    bot.start()
