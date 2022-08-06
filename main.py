
from os import getenv
from dataclasses import (
    dataclass,
    fields
)
from contextlib import AsyncExitStack

from aiogram import (
    Bot,
    Dispatcher,
    executor,
)
from aiogram.types import ParseMode

import aiobotocore.session


#######
#
#   SECRETS
#
######

# Ask @alexkuk for .env


BOT_TOKEN = getenv('BOT_TOKEN')

AWS_KEY_ID = getenv('AWS_KEY_ID')
AWS_KEY = getenv('AWS_KEY')

DYNAMO_ENDPOINT = getenv('DYNAMO_ENDPOINT')


######
#
#   OBJ
#
#####


def obj_annots(obj):
    for field in fields(obj):
        yield field.name, field.type


####
#   VOTING
######


@dataclass
class User:
    user_id: int
    intro: str


######
#
#  DYNAMO
#
######


######
#   MANAGER
######


async def dynamo_client():
    session = aiobotocore.session.get_session()
    manager = session.create_client(
        'dynamodb',

        # Always ru-central1 for YC
        # https://cloud.yandex.ru/docs/ydb/docapi/tools/aws-setup
        region_name='ru-central1',

        endpoint_url=DYNAMO_ENDPOINT,
        aws_access_key_id=AWS_KEY_ID,
        aws_secret_access_key=AWS_KEY,
    )

    # https://github.com/aio-libs/aiobotocore/discussions/955
    exit_stack = AsyncExitStack()
    client = await exit_stack.enter_async_context(manager)
    return exit_stack, client


######
#  OPS
#####


N = 'N'
S = 'S'


async def dynamo_put(client, table, item):
    await client.put_item(
        TableName=table,
        Item=item
    )


async def dynamo_get(client, table, key_name, key_type, key_value):
    response = await client.get_item(
        TableName=table,
        Key={
            key_name: {
                key_type: str(key_value)
            }
        }
    )
    return response.get('Item')


async def dynamo_delete(client, table, key_name, key_type, key_value):
    await client.delete_item(
        TableName=table,
        Key={
            key_name: {
                key_type: str(key_value)
            }
        }
    )


######
#   DE/SERIALIZE
####


def dynamo_type(annot):
    if annot == int:
        return N
    elif annot == str:
        return S


def dynamo_parse_value(value, annot):
    if annot == int:
        return int(value)
    elif annot == str:
        return value


def dynamo_format_value(value, annot):
    if annot == int:
        return str(value)
    elif annot == str:
        return value


def dynamo_parse_item(item, cls):
    kwargs = {}
    for name, annot in obj_annots(cls):
        type = dynamo_type(annot)
        value = item[name][type]
        value = dynamo_parse_value(value, annot)
        kwargs[name] = value
    return cls(**kwargs)


def dynamo_format_item(obj):
    item = {}
    for name, annot in obj_annots(obj):
        value = getattr(obj, name)
        value = dynamo_format_value(value, annot)
        type = dynamo_type(annot)
        item[name] = {type: value}
    return item


######
#   READ/WRITE
######


USERS_TABLE = 'users'
USER_ID_KEY = 'user_id'


async def put_user(db, user):
    item = dynamo_format_item(user)
    await dynamo_put(db.client, USERS_TABLE, item)


async def get_user(db, user_id):
    item = await dynamo_get(
        db.client, USERS_TABLE,
        USER_ID_KEY, N, user_id
    )
    if not item:
        return
    return dynamo_parse_item(item, User)


async def delete_user(db, user_id):
    await dynamo_delete(
        db.client, USERS_TABLE,
        USER_ID_KEY, N, user_id
    )


######
#  DB
#######


class DB:
    def __init__(self):
        self.exit_stack = None
        self.client = None

    async def connect(self):
        self.exit_stack, self.client = await dynamo_client()

    async def close(self):
        await self.exit_stack.aclose()


DB.put_user = put_user
DB.get_user = get_user
DB.delete_user = delete_user


#####
#
#  HANDLERS
#
#####


START_COMMAND = 'start'
EDIT_INTRO_COMMAND = 'edit_intro'
SHOW_INTRO_COMMAND = 'show_intro'

START_TEXT = f'''<b>Что это?</b>
Бот Нелюдим раз в неделю предлагает встречу со случайным \
собеседником из чатика @natural_language_processing.

<b>Зачем? В чем польза?</b>

<b>Как это работает?</b>

<b>С чего начать</b>

<b>Команды</b>

/{EDIT_INTRO_COMMAND} — заполнить/поменять интро
/{SHOW_INTRO_COMMAND} — как другие видят твое интро
'''


async def handle_start(context, message):
    await message.answer(text=START_TEXT)


def setup_handlers(context):
    context.dispatcher.register_message_handler(context.handle_start)


#######
#
#  BOT
#
#######


########
#   WEBHOOK
######


async def on_startup(context, _):
    await context.db.connect()


async def on_shutdown(context, _):
    await context.db.close()


PORT = getenv('PORT', 8080)


def run(context):
    executor.start_webhook(
        dispatcher=context.dispatcher,

        webhook_path='/',
        port=PORT,

        on_startup=context.on_startup,
        on_shutdown=context.on_shutdown,

        # Disable aiohttp "Running on ... Press CTRL+C"
        # Polutes YC Logging
        print=None
    )


########
#   CONTEXT
######


class BotContext:
    def __init__(self):
        self.bot = Bot(
            token=BOT_TOKEN,
            parse_mode=ParseMode.HTML,
        )
        self.dispatcher = Dispatcher(self.bot)
        self.db = DB()


BotContext.handle_start = handle_start

BotContext.setup_handlers = setup_handlers

BotContext.on_startup = on_startup
BotContext.on_shutdown = on_shutdown
BotContext.run = run


######
#
#   MAIN
#
#####


if __name__ == '__main__':
    context = BotContext()
    context.setup_handlers()
    context.run()
