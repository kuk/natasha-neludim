
from .bot.bot import (
    init_bot,
    bot_dispatcher
)
from .db import DB
from .schedule import Schedule


class Context:
    def __init__(self):
        self.bot = init_bot()
        self.dispatcher = bot_dispatcher(self.bot)
        self.db = DB()
        self.schedule = Schedule()
