import asyncio
import websockets
import aiohttp
import ujson as json


class UnexpectedResponseCode(ValueError):
    pass


class SlackClient(object):
    slack_api = 'https://slack.com/api'

    def __init__(self, token):
        self.token = token

    async def real_time_messaging(self, consumer):
        connection = await self.api_call('rtm.start')
        url = connection['url']
        async with websockets.connect(url) as websocket:
            while True:
                data = await websocket.recv()
                message = json.loads(data)
                await consumer(message)

    async def api_call(self, path, **data):
        data = data or {}
        data['token'] = self.token
        url = '{}/{}'.format(self.slack_api, path)
        form = aiohttp.FormData(data)
        with aiohttp.ClientSession() as session:
            async with session.post(url, data=form) as response:
                if response.status != 200:
                    raise UnexpectedResponseCode(response.status)
                return await response.json()


async def echo(message):
    print(message)


if __name__ == "__main__":
    import os
    token = os.environ['SLACK_TOKEN']
    sc = SlackClient(token)
    rtm = sc.real_time_messaging(echo)

    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    response = loop.run_until_complete(rtm)
    loop.close()
