
from aiogram.types import ChatType
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from neludim.log import (
    log,
    json_msg
)


class PrivateMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message, data):
        if message.chat.type != ChatType.PRIVATE:
            raise CancelHandler


class LoggingMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message, data):
        log.info(json_msg(
            user_id=message.from_user.id,
            text=message.text
        ))


def setup_middlewares(context):
    middlewares = [
        PrivateMiddleware(),
        LoggingMiddleware(),
    ]
    for middleware in middlewares:
        context.dispatcher.middleware.setup(middleware)
