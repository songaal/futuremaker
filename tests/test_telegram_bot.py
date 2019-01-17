import asyncio
import json
import random
import threading
import time

import aiohttp
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from futuremaker.collections import expiredict
from futuremaker.log import logger

class test_result(object):
    def yes(self, param):
        print("yes")
        return "주문을 요청하였습니다."
    def no(self, param):
        print("no")
        return "주문을 취소하였습니다."

class TelegramBotAdapter(object):

    def __init__(self, bot_token=None, chat_id=None, message_handler={}, expire_time=60, expired_handler=None):
        self.bot_id = str(random.randint(random.randint(1, 99), random.randint(100, 9999)))
        self.bot_token = bot_token
        self.bot = Bot(bot_token)
        self.send_count = 0
        self.chat_id = chat_id
        self.message_handler = message_handler
        if expired_handler is not None:
            self.question_tmp = expiredict(expired_handler)
        else:
            self.question_tmp = expiredict(expire_time=expire_time,
                                           expired_callback=self.expired_question)

        # ========== TEST =============
        def send_test():
            time.sleep(3)
            ss = test_result()
            self.send_question(f'''주문을 결정해주세요. \n가격: {str(random.randint(3000, 999999))}\n이유: "볼린져밴드 상승 중입니다!!!!"''',
                               yes_func=ss.yes, yes_param={"aa": "bbb"})
        threading.Thread(target=send_test, daemon=True).start()
        # ========== TEST =============

        self._watch_update()

    def expired_question(self, question):
        self.bot.edit_message_text(chat_id=question["message"]["chat_id"],
                                   message_id=question["message"]["message_id"],
                                   text=f"{question['message']['text']}\n결과 >> 시간초과",
                                   parse_mode="HTML")

    def send(self, text="", reply_markup=None):
        send_text = f"BOT ID: {self.bot_id}\n" + text
        return self.bot.send_message(text=send_text,
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
                bot_id = text.split("\n")[0].split(":")[1].strip()
                if self.bot_id != bot_id:
                    logger.debug("다른 봇 메시지는 무시합니다.")
                    return
                question = self.question_tmp.get(message_id)
                del self.question_tmp[message_id]
                if choice == "YES":
                    logger.debug("selected: YES")
                    if question['yes_func'] is not None:
                        result = question['yes_func'](question['yes_param'])
                else:
                    logger.debug("selected: No")
                    if question['no_func'] is not None:
                        result = question['no_func'](question['no_param'])

                self.bot.edit_message_text(chat_id=question["message"]["chat_id"],
                                           message_id=question["message"]["message_id"],
                                           text=f"{question['message']['text']}\n결과 >> {result}",
                                           parse_mode="HTML")
        except KeyError:
            logger.error(KeyError)

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

                                        self.question_tmp.lock()
                                        self.distribute(update_type, str(message_id), text, choice)
                                        self.question_tmp.unlook()
                                    except KeyError:
                                        logger.error("key error", KeyError)

                    # 한번씩 쉬면서 대화 내용 조회하기.
                    time.sleep(1)
        loop = asyncio.get_event_loop()
        loop.create_task(get_update())

        # 테스트에서만 사용.
        # loop.run_forever()


trader_bot = TelegramBotAdapter("589994875:AAG2KC96wcVCe95SygjbxkEpUCV26TBwF7A", 455272535)
# trader_bot.run_watch_update()


# # telegram_bot = TelegramBot("751644657", "AAEsCImLyP9MuRAWahCwIlgf8XBIMINlCpY", "455272535")
# # telegram_bot.run()
#
# # "https://api.telegram.org/bot751644657:AAEsCImLyP9MuRAWahCwIlgf8XBIMINlCpY/getUpdates"
#
# def start(bot, update):
#     keyboard = [[InlineKeyboardButton("Option 1", url="http://naver.com", callback_data='1'),
#                  InlineKeyboardButton("Option 2", callback_data='2')],
#                 [InlineKeyboardButton("Option 3", callback_data='3')]]
#
#     reply_markup = InlineKeyboardMarkup(keyboard)
#
#     result = update.message.reply_text('Please choose:', reply_markup=reply_markup)
# #     result = update.message.reply_html('''<b>bold</b>, <strong>bold</strong>
# # <i>italic</i>, <em>italic</em>
# # <a href="http://www.example.com/">inline URL</a>
# # <a href="tg://user?id=123456789">inline mention of a user</a>
# # <code>inline fixed-width code</code>
# # <pre>pre-formatted fixed-width code block</pre>
# #     ''')
# #     message_id = result["message_id"]
#     # time.sleep(3)
#     # bot.edit_message_text(text="Selected option:",
#     #                       chat_id="455272535",
#     #                       message_id=message_id)
#
#
# def button(bot, update):
#     query = update.callback_query
#     keyboard = [[InlineKeyboardButton("Option " + str(random.randint(1, 100)), url="http://google.com", callback_data='1'),
#                  InlineKeyboardButton("Option " + str(random.randint(1, 100)), callback_data='2')],
#                 [InlineKeyboardButton("Option " + str(random.randint(1, 100)), callback_data='3')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#
#     # result = update.message.reply_text('Please choose:', reply_markup=reply_markup)
#
#     bot.edit_message_reply_markup(chat_id=query.message.chat_id,
#                                   reply_markup=reply_markup,
#                                   message_id=query.message.message_id)
#
#     bot.edit_message_text(text="Selected option: {}".format(query.data),
#                           chat_id=query.message.chat_id,
#                           message_id=query.message.message_id)
#
#
# def help(bot, update):
#     update.message.reply_text("Use /start to test this bot.")
#
#
# def error(bot, update, error):
#     """Log Errors caused by Updates."""
#     logger.warning('Update "%s" caused error "%s"', update, error)
#
#
#
#

