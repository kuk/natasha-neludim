
import asyncio
from dataclasses import dataclass

from aiogram import exceptions

from neludim.log import (
    log,
    json_msg
)


# https://github.com/aiogram/aiogram/blob/dev-2.x/examples/broadcast_example.py


async def send_message(bot, chat_id, text):
    try:
        await bot.send_message(chat_id, text)
    except exceptions.RetryAfter as error:
        await asyncio.sleep(error.timeout)
        await send_message(bot, chat_id, text)
    except exceptions.TelegramAPIError as error:
        return error.__class__.__name__
    else:
        return


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
            error = await send_message(self.bot, message.chat_id, message.text)
            log.info(json_msg(
                chat_id=message.chat_id,
                error=error
            ))

            # safe 20 rps < limit 30 rps
            await asyncio.sleep(0.05)
