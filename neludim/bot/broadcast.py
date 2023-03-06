
import asyncio
from dataclasses import dataclass

from aiogram import exceptions


@dataclass
class BroadcastResult:
    chat_id: int
    message_id: int = None
    error: str = None


class Broadcast:
    def __init__(self, bot):
        self.bot = bot
        self.reset()

    def reset(self):
        self.results = []

    async def send_message(self, chat_id, text, reply_markup=None):
        # https://github.com/aiogram/aiogram/blob/dev-2.x/examples/broadcast_example.py
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup
            )
            result = BroadcastResult(
                chat_id=chat_id,
                message_id=message.message_id,
            )

        except exceptions.TelegramAPIError as error:
            result = BroadcastResult(
                chat_id=chat_id,
                error=error.__class__.__name__
            )
        self.results.append(result)

        # https://habr.com/ru/post/543676/
        # Не больше одного сообщения в секунду в один чат,
        # Не больше 30 сообщений в секунду вообще
        await asyncio.sleep(1 / 30)
