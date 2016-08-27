class BotPlugin(object):
    def __init__(self, bot):
        self.bot = bot

    async def event_transform(self, event):
        return event

    def help(self):
        return {}

    @property
    def handlers(self):
        handlers = {}
        for name in dir(self):
            if name.startswith("on_"):
                func = getattr(self, name)
                if callable(func):
                    handlers[name[3:]] = [func, ]
        return handlers
