
from aiogram.types import ChatType
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from neludim.log import (
    log,
    json_msg
)


class PrivateMiddleware(BaseMiddleware):
    def on_pre_process(self, type):
        if type != ChatType.PRIVATE:
            raise CancelHandler

    async def on_pre_process_message(self, message, data):
        self.on_pre_process(message.chat.type)

    async def on_pre_process_callback_query(self, query, data):
        self.on_pre_process(query.message.chat.type)


class LoggingMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message, data):
        log.info(json_msg(
            user_id=message.from_user.id,
            text=message.text
        ))

    async def on_pre_process_callback_query(self, query, data):
        log.info(json_msg(
            user_id=query.from_user.id,
            data=query.data
        ))


def setup_middlewares(context):
    middlewares = [
        PrivateMiddleware(),
        LoggingMiddleware(),
    ]
    for middleware in middlewares:
        context.dispatcher.middleware.setup(middleware)
