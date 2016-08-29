import traceback
from functools import wraps


def exception_eater(fxn):
    @wraps(fxn)
    def _(*args, **kwargs):
        try:
            return fxn(*args, **kwargs)
        except Exception as e:
            print("{}: {}".format(fxn.__name__, e))
            traceback.print_exc()
    return _


def exception_eater_async(fxn):
    @wraps(fxn)
    async def _(*args, **kwargs):
        try:
            return await fxn(*args, **kwargs)
        except Exception as e:
            print("{}: {}".format(fxn.__name__, e))
            traceback.print_exc()
    return _
