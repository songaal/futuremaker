import asyncio
import json
import random
import time

import aiohttp
# from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from futuremaker.collections import expiredict
from futuremaker.log import logger


class TelegramBotAdapter(object):

    def __init__(self, bot_id=None, bot_token=None, chat_id=None, message_handler={},
                 expire_time=60, expired_handler=None):
        if bot_token is None:
            logger.debug("Telegram Bot Disabled.")
            return
        if bot_id is None or bot_id == "":
            self.bot_id = str(random.randint(random.randint(1, 99), random.randint(100, 9999)))
        else:
            self.bot_id = bot_id
        logger.debug("Telegram Bot ID. %s", self.bot_id)
        self.bot_token = bot_token
        self._bot = Bot(bot_token)
        self.chat_id = chat_id
        self.message_handler = message_handler
        if expired_handler is not None:
            self.question_tmp = expiredict(expired_handler)
        else:
            self.question_tmp = expiredict(expire_time=expire_time,
                                           expired_callback=self.expired_question)
        self._watch_update()

    def expired_question(self, question):
        self._bot.edit_message_text(chat_id=question["message"]["chat_id"],
                                   message_id=question["message"]["message_id"],
                                   text=f"{question['message']['text']}\n결과 >> 시간초과",
                                   parse_mode="HTML")

    def send(self, text="", reply_markup=None):
        send_text = f"BOT ID: {self.bot_id}\n" + text
        return self._bot.send_message(text=send_text,
                                      parse_mode="HTML",
                                      chat_id=self.chat_id,
                                      reply_markup=reply_markup)

    def send_question(self, question_text="",
                      yes_name="Yes", yes_func=None, yes_param=None,
                      no_name="No", no_func=None, no_param=None):
        keyboard = [[InlineKeyboardButton(yes_name, callback_data='YES'),
                     InlineKeyboardButton(no_name, callback_data='NO')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = self.send(question_text, reply_markup)
        message_id = str(message["message_id"])
        self.question_tmp[message_id] = {
            "message": message,
            "yes_func": yes_func,
            "yes_param": yes_param,
            "no_func": no_func,
            "no_param": no_param
        }
        return self.question_tmp.get(message_id)

    def distribute(self, update_type, message_id, text, choice=None):
        try:
            logger.debug("==============================================")
            logger.debug("새로운 메시지가 도착했습니다.")
            logger.debug(f"[{update_type}] message_id: {message_id}, choice: {choice}")
            logger.debug(f"{text}")
            logger.debug("==============================================")
            if update_type == "message":
                # TODO 메시지로 도착했을때 명령어 기능 추가하면 좋을듯..
                logger.debug("[미개발..] %s", text)

            elif update_type == "callback_query":
                # 요청한 봇이 맞는지 확인한다.
                bot_id = text.split("\n")[0].split(":")[1].strip()
                if self.bot_id != bot_id:
                    logger.debug("다른 봇 메시지는 무시합니다.")
                    return

                # 임시저장된 내용 가져온수 삭제처리.
                self.question_tmp.lock()
                question = self.question_tmp.get(message_id)
                del self.question_tmp[message_id]
                self.question_tmp.unlock()

                # 버튼을 지운다.
                self._bot.edit_message_text(chat_id=question["message"]["chat_id"],
                                            message_id=question["message"]["message_id"],
                                            text=f"{question['message']['text']}",
                                            parse_mode="HTML")
                # 선택에 따라서 함수 호출한다.
                result = None
                if choice == "YES":
                    logger.debug("selected: YES")
                    if question['yes_func'] is not None:
                        result = question['yes_func'](question['yes_param'])

                else:
                    logger.debug("selected: No")
                    if question['no_func'] is not None:
                        result = question['no_func'](question['no_param'])

                # 결과를 전송한다.
                if result is None:
                    result = "No Data"
                self._bot.edit_message_text(chat_id=question["message"]["chat_id"],
                                            message_id=question["message"]["message_id"],
                                            text=f"{question['message']['text']}\n결과 >> {result}",
                                            parse_mode="HTML")
        except KeyError:
            # ignore 요청의 두번 답을 말할경우.
            pass

    def _watch_update(self):
        async def get_update():
            async with aiohttp.ClientSession() as session:
                offset = 0
                limit = 50
                current_ts = int(time.time())
                while True:
                    url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates?offset={offset + 1}&limit={limit}"
                    async with session.get(url) as response:
                        data = json.loads(await response.text())
                        if data["ok"]:
                            results = data["result"]
                            for result in results:
                                for update_type in result.keys():
                                    try:
                                        date = None
                                        text = None
                                        choice = None
                                        message_id = None
                                        if update_type == "message":
                                            date = result["message"]["date"]
                                            text = result["message"]["text"]
                                            message_id = result["message"]["message_id"]

                                        elif update_type == "callback_query":
                                            date = result["callback_query"]["message"]["date"]
                                            text = result["callback_query"]["message"]["text"]
                                            message_id = result["callback_query"]["message"]["message_id"]
                                            choice = result["callback_query"]["data"]

                                        if update_type == "update_id" or current_ts >= date:
                                            # 이전 메시지 무시..
                                            offset = result["update_id"]
                                            continue

                                        self.distribute(update_type, str(message_id), text, choice)
                                    except KeyError:
                                        logger.error("key error", KeyError)
                    # 한번씩 쉬면서 대화 내용 조회하기.
                    time.sleep(1)
        loop = asyncio.get_event_loop()
        loop.create_task(get_update())
