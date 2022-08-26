
import asyncio

from aiogram import exceptions


# https://github.com/aiogram/aiogram/blob/dev-2.x/examples/broadcast_example.py


async def send_message(bot, chat_id, text):
    try:
        await bot.send_message(chat_id, text)
    except exceptions.RetryAfter as error:
        await asyncio.sleep(error.timeout)
        await send_message(bot, chat_id, text)
    except exceptions.TelegramAPIError:
        pass


class Broadcast:
    def __init__(self, bot):
        self.bot = bot

    async def send_message(self, chat_id, text):
        await send_message(self.bot, chat_id, text)
