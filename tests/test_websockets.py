import asyncio
import unittest

import websockets


class TestWebsockets(unittest.TestCase):

    def test_echo(self):

        async def echo(websocket, path):
            print('path>', path)
            async for message in websocket:
                await websocket.send(message)

        asyncio.get_event_loop().run_until_complete(
            websockets.serve(echo, 'localhost', 8765))
        asyncio.get_event_loop().run_forever()

    def test_client(self):
        async def hello():
            async with websockets.connect(
                    'ws://localhost:8765') as websocket:
                name = input("What's your name? ")

                await websocket.send(name)
                print(f"> {name}")

                greeting = await websocket.recv()
                print(f"< {greeting}")

        asyncio.get_event_loop().run_until_complete(hello())

    def test_client(self):
        async def handle_message(message):
            print(f'< {message}')


        async def hello():
            async with websockets.connect(
                    'wss://www.bitmex.com/realtime') as websocket:
                await websocket.send('{"op": "subscribe", "args": ["tradeBin1m:XBTUSD"]}')
                while True:
                    message = await websocket.recv()
                    await handle_message(message)


        asyncio.get_event_loop().run_until_complete(hello())