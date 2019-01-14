import unittest

from futuremaker import utils


class TestTelegram(unittest.TestCase):

    def test_send(self):
        async def go():
            await utils.send_telegram('We have created for you a selection of fun projects, that can show you how to create '
                            'application from the blog to the applications related to data science')

        utils.test_async(go())