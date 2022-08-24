
import asyncio
from dataclasses import dataclass

from aiogram import exceptions


@dataclass
class BroadcastTask:
    chat_id: int
    text: str


# https://github.com/aiogram/aiogram/blob/dev-2.x/examples/broadcast_example.py


async def send_message(bot, chat_id, text):
    try:
        await bot.send_message(chat_id, text)
    except exceptions.RetryAfter as error:
        await asyncio.sleep(error.timeout)
        await send_message(bot, chat_id, text)
    except exceptions.TelegramAPIError:
        pass


async def broadcast(bot, tasks, delay=0.05):
    # 20 messages per second (Limit: 30 messages per second)

    for task in tasks:
        await send_message(bot, task.chat_id, task.text)
        await asyncio.sleep(delay)
