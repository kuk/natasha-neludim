
import asyncio
from dataclasses import dataclass

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


@dataclass
class Message:
    chat_id: int
    text: str


class Broadcast:
    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    async def queue_message(self, chat_id, text):
        message = Message(chat_id, text)
        self.queue.append(message)

    async def send(self):
        for message in self.queue:
            await send_message(self.bot, message.chat_id, message.text)

            # safe 20 rps < limit 30 rps
            await asyncio.sleep(0.05)
