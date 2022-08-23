
from .bot.bot import bot_dispatcher
from .db import DB
from .schedule import Schedule


class Context:
    def __init__(self):
        self.bot, self.dispatcher = bot_dispatcher()
        self.db = DB()
        self.schedule = Schedule()
