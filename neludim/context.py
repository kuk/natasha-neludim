
from .bot.bot import (
    init_bot,
    Dispatcher
)
from .bot.broadcast import Broadcast
from .db import DB
from .schedule import Schedule


class Context:
    def __init__(self):
        self.bot = init_bot()
        self.dispatcher = Dispatcher(self.bot)
        self.broadcast = Broadcast(self.bot)
        self.db = DB()
        self.schedule = Schedule()
