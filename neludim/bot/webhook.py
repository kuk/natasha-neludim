
from functools import partial

from aiogram import executor

from neludim.const import PORT


async def on_startup(context, _):
    await context.db.connect()


async def on_shutdown(context, _):
    await context.db.close()


def start_webhook(context):
    executor.start_webhook(
        dispatcher=context.dispatcher,

        webhook_path='/',
        port=PORT,

        on_startup=partial(on_startup, context),
        on_shutdown=partial(on_shutdown, context),

        # Disable aiohttp "Running on ... Press CTRL+C"
        # Polutes YC Logging
        print=None
    )
