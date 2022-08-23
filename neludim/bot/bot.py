
from aiogram import (
    Bot,
    Dispatcher,
)
from aiogram.types import ParseMode

from neludim.const import BOT_TOKEN


def bot_dispatcher():
    bot = Bot(
        token=BOT_TOKEN,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    dispatcher = Dispatcher(bot)
    return bot, dispatcher
