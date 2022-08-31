
import asyncio
from dataclasses import dataclass

from aiogram import exceptions

from neludim.log import (
    log,
    json_msg
)


@dataclass
class Message:
    chat_id: int
    text: str


async def send_message(bot, chat_id, text):
    # https://github.com/aiogram/aiogram/blob/dev-2.x/examples/broadcast_example.py

    try:
        await bot.send_message(chat_id, text)
    except exceptions.RetryAfter as error:
        await asyncio.sleep(error.timeout)
        await send_message(bot, chat_id, text)
    except exceptions.TelegramAPIError as error:
        return error.__class__.__name__
    else:
        return


async def producer(queue, messages, max_rps):
    for message in messages:
        await queue.put(message)
        await asyncio.sleep(1 / max_rps)


async def worker(bot, queue):
    while True:
        message = await queue.get()
        error = await send_message(bot, message.chat_id, message.text)
        log.info(json_msg(
            chat_id=message.chat_id,
            error=error
        ))
        queue.task_done()


async def broadcast(bot, messages, pool_size=5, max_rps=30):
    # https://gist.github.com/showa-yojyo/4ed200d4c41f496a45a7af2612912df3

    # https://habr.com/ru/post/543676/
    # Не больше одного сообщения в секунду в один чат,
    # Не больше 30 сообщений в секунду вообще

    queue = asyncio.Queue()
    tasks = [
        asyncio.create_task(worker(bot, queue))
        for _ in range(pool_size)
    ]

    await producer(queue, messages, max_rps)
    await queue.join()

    for task in tasks:
        task.cancel()
    await asyncio.gather(
        *tasks,
        return_exceptions=True
    )
