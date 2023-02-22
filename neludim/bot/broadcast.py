
import asyncio

from aiogram import exceptions


class Broadcast:
    def __init__(self, bot):
        self.bot = bot
        self.reset()

    def reset(self):
        self.errors = {}

    async def send_message(self, chat_id, text, reply_markup=None):
        # https://github.com/aiogram/aiogram/blob/dev-2.x/examples/broadcast_example.py
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup
            )

        except exceptions.TelegramAPIError as error:
            # Common case: BotBlocked exceptions
            self.errors[chat_id] = error.__class__.__name__

        # https://habr.com/ru/post/543676/
        # Не больше одного сообщения в секунду в один чат,
        # Не больше 30 сообщений в секунду вообще
        await asyncio.sleep(1 / 30)
