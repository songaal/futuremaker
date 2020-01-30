import asyncio

from futuremaker import utils


class Test:
    def __init__(self):
        self.telegram_bot_token='852670167:AAExawLUJfb-lGKVHQkT5mthCTEOT_BaQrg'
        self.telegram_chat_id='352354994'

    async def send_telegram(self, text):
        if self.telegram_bot_token and self.telegram_chat_id:
            return await utils.send_telegram(self.telegram_bot_token, self.telegram_chat_id, text)

# t = Test()
# c = t.send_telegram('ㅎㅏ이루!')
# print(c)
# asyncio.get_event_loop().run_until_complete(c)
# asyncio.run(c)
# print(asyncio.get_event_loop().is_running())

# async def main2():
    # t = Test()
    # print(await t.send_telegram('ㅎㅏ이루!'))
text = '하이루!!!!~~~'
c = utils.send_telegram('852670167:AAExawLUJfb-lGKVHQkT5mthCTEOT_BaQrg', '352354994', text)
loop = asyncio.get_event_loop()
loop.run_until_complete(c)


# asyncio.run(main2())
