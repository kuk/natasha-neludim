
import json
import logging
from os import getenv
from dataclasses import (
    dataclass,
    fields,
    is_dataclass,
)
from contextlib import AsyncExitStack
from contextvars import ContextVar

from aiogram import (
    Bot,
    Dispatcher,
    executor,
)
from aiogram.types import (
    ParseMode,
    ChatType,
    BotCommand,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import CancelHandler

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
#   LOGGER
#
#######


LOG_LEVEL = getenv('LOG_LEVEL', logging.INFO)

log = logging.getLogger(__name__)
log.setLevel(LOG_LEVEL)
log.addHandler(logging.StreamHandler())


def json_msg(**kwargs):
    return json.dumps(
        kwargs,
        ensure_ascii=False
    )


######
#
#   OBJ
#
#####


def obj_annots(obj):
    for field in fields(obj):
        yield field.name, field.type


####
#   USER
######


EDIT_NAME_STATE = 'edit_name'
EDIT_CITY_STATE = 'edit_city'
EDIT_LINKS_STATE = 'edit_links'


@dataclass
class Intro:
    name: str = None
    city: str = None
    links: str = None


@dataclass
class User:
    user_id: int
    username: str = None
    state: str = None
    intro: Intro = None


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
M = 'M'


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
    elif is_dataclass(annot):
        return M


def dynamo_parse_value(value, annot):
    if annot == int:
        return int(value)
    elif annot == str:
        return value
    elif is_dataclass(annot):
        return dynamo_parse_item(value, annot)


def dynamo_format_value(value, annot):
    if annot == int:
        return str(value)
    elif annot == str:
        return value
    elif is_dataclass(annot):
        return dynamo_format_item(value)


def dynamo_parse_item(item, cls):
    kwargs = {}
    for name, annot in obj_annots(cls):
        if name in item:
            type = dynamo_type(annot)
            value = item[name][type]
            value = dynamo_parse_value(value, annot)
        else:
            value = None
        kwargs[name] = value
    return cls(**kwargs)


def dynamo_format_item(obj):
    item = {}
    for name, annot in obj_annots(obj):
        value = getattr(obj, name)
        if value is not None:
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


######
#   COMMAND
######


START_COMMAND = 'start'

EDIT_INTRO_COMMAND = 'edit_intro'
EDIT_NAME_COMMAND = 'edit_name'
EDIT_CITY_COMMAND = 'edit_city'
EDIT_LINKS_COMMAND = 'edit_links'

CANCEL_COMMAND = 'cancel'
EMPTY_COMMAND = 'empty'

PAUSE_COMMAND = 'pause'
UNPAUSE_COMMAND = 'unpause'


COMMAND_DESCRIPTIONS = {
    EDIT_INTRO_COMMAND: 'поменять анкету',
    EDIT_NAME_COMMAND: 'поменять имя',
    EDIT_CITY_COMMAND: 'поменять город',
    EDIT_LINKS_COMMAND: 'поменять ссылки',

    CANCEL_COMMAND: 'отменить',
    EMPTY_COMMAND: 'оставить пустым',

    PAUSE_COMMAND: 'не участвовать во встречах',
    UNPAUSE_COMMAND: 'снова участвовать',
}


#####
#  TEXT
####


def command_description(command):
    return f'/{command} — {COMMAND_DESCRIPTIONS[command]}'


START_TEXT = f'''Бот раз в неделю предлагает встречу со случайным \
собеседником из чатика @natural_language_processing.

В понедельник бот присылает пару. В воскресенье спрашивает будешь ли \
участвовать на следующей неделе.

{command_description(EDIT_INTRO_COMMAND)}
{command_description(PAUSE_COMMAND)}
{command_description(UNPAUSE_COMMAND)}
'''


def format_empty(value):
    if value is None:
        return '∅'
    return value


EDIT_INTRO_TEXT = f'''Имя: {{name}}
Город: {{city}}
Ссылки: {{links}}

{command_description(EDIT_NAME_COMMAND)}
{command_description(EDIT_CITY_COMMAND)}
{command_description(EDIT_LINKS_COMMAND)}

{command_description(CANCEL_COMMAND)}
{command_description(EMPTY_COMMAND)}
'''

EDIT_NAME_TEXT = '''Напиши настоящее имя. Собеседник поймёт, как \
к тебе обращаться.'''

EDIT_CITY_TEXT = '''Напиши город, в котором живёшь. Собеседник \
поймет предлагать оффлайн встречу или нет.'''

EDIT_LINKS_TEXT = '''Накидай ссылок про себя: блог, твиттер, фейсбук, \
канал, подкаст. Собеседник поймёт чем ты занимаешься, о чём интересно \
спросить. Снимает неловкость в начале разговора.

Примеры
- http://lab.alexkuk.ru, https://github.com/kuk, \
https://habr.com/ru/users/alexanderkuk/
- https://www.linkedin.com/in/alexkuk/, https://vk.com/alexkuk
- http://val.maly.hk'''

TOP_CITIES = [
    'Москва',
    'Санкт-Петербург',
    'Киев',
    'Минск',
    'Лондон',
    'Берлин',
]


######
#  START
######


async def handle_start(context, message):
    user = context.user.get()
    if not user:
        user = User(
            user_id=message.from_user.id,
            username=message.from_user.username,
            intro=Intro(
                name=message.from_user.full_name,
            )
        )
        context.user.set(user)

    await context.bot.set_my_commands(commands=[
        BotCommand(command, description)
        for command, description
        in COMMAND_DESCRIPTIONS.items()
    ])

    await message.answer(text=START_TEXT)


#####
#  INTRO
######


def format_edit_intro_text(user):
    return EDIT_INTRO_TEXT.format(
        name=format_empty(user.intro.name),
        city=format_empty(user.intro.city),
        links=format_empty(user.intro.links)
    )


async def handle_edit_intro(context, message):
    user = context.user.get()
    text = format_edit_intro_text(user)
    await message.answer(text=text)


async def handle_edit_name(context, message):
    user = context.user.get()
    user.state = EDIT_NAME_STATE

    markup = None
    if not user.intro.name and message.from_user.full_name:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(message.from_user.full_name)

    await message.answer(
        text=EDIT_NAME_TEXT,
        reply_markup=markup
    )


async def handle_edit_city(context, message):
    user = context.user.get()
    user.state = EDIT_CITY_STATE

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for city in TOP_CITIES:
        markup.insert(KeyboardButton(city))

    await message.answer(
        text=EDIT_CITY_TEXT,
        reply_markup=markup
    )


async def handle_edit_links(context, message):
    user = context.user.get()
    user.state = EDIT_LINKS_STATE

    await message.answer(text=EDIT_LINKS_TEXT)


def command_text(command):
    return f'/{command}'


async def handle_edit_states(context, message):
    user = context.user.get()

    if message.text != command_text(CANCEL_COMMAND):
        if message.text != command_text(EMPTY_COMMAND):
            value = message.text
        else:
            value = None

        if user.state == EDIT_NAME_STATE:
            user.intro.name = value
        elif user.state == EDIT_CITY_STATE:
            user.intro.city = value
        elif user.state == EDIT_LINKS_STATE:
            user.intro.links = value

    user.state = None
    text = format_edit_intro_text(user)
    await message.answer(
        text=text,
        reply_markup=ReplyKeyboardRemove()
    )


#######
#   SETUP
######


def setup_handlers(context):
    context.dispatcher.register_message_handler(
        context.handle_start,
        commands=START_COMMAND,
    )

    context.dispatcher.register_message_handler(
        context.handle_edit_intro,
        commands=EDIT_INTRO_COMMAND
    )
    context.dispatcher.register_message_handler(
        context.handle_edit_name,
        commands=EDIT_NAME_COMMAND,
    )
    context.dispatcher.register_message_handler(
        context.handle_edit_city,
        commands=EDIT_CITY_COMMAND,
    )
    context.dispatcher.register_message_handler(
        context.handle_edit_links,
        commands=EDIT_LINKS_COMMAND,
    )
    context.dispatcher.register_message_handler(
        context.handle_edit_states,
        user_states=[
            EDIT_NAME_STATE,
            EDIT_CITY_STATE,
            EDIT_LINKS_STATE,
        ]
    )


#####
#
#  FILTER
#
####


class UserStatesFilter(BoundFilter):
    context = None
    key = 'user_states'

    def __init__(self, user_states):
        self.user_states = user_states

    async def check(self, obj):
        user = self.context.user.get()
        return user and user.state in self.user_states


def setup_filters(context):
    UserStatesFilter.context = context
    context.dispatcher.filters_factory.bind(UserStatesFilter)


######
#
#   MIDDLEWARE
#
######


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


class UserMiddleware(BaseMiddleware):
    def __init__(self, context):
        self.context = context
        BaseMiddleware.__init__(self)

    async def on_pre_process_message(self, message, data):
        user = await self.context.db.get_user(message.from_user.id)
        self.context.user.set(user)

    async def on_post_process_message(self, message, results, data):
        user = self.context.user.get()
        if user:
            await self.context.db.put_user(user)


def setup_middlewares(context):
    middlewares = [
        PrivateMiddleware(),
        LoggingMiddleware(),
        UserMiddleware(context),
    ]
    for middleware in middlewares:
        context.dispatcher.middleware.setup(middleware)


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


USER_VAR = 'user'


class BotContext:
    def __init__(self):
        self.bot = Bot(
            token=BOT_TOKEN,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        self.dispatcher = Dispatcher(self.bot)
        self.db = DB()

        self.user = ContextVar(USER_VAR)


BotContext.handle_start = handle_start
BotContext.handle_edit_intro = handle_edit_intro
BotContext.handle_edit_name = handle_edit_name
BotContext.handle_edit_city = handle_edit_city
BotContext.handle_edit_links = handle_edit_links
BotContext.handle_edit_states = handle_edit_states

BotContext.setup_middlewares = setup_middlewares
BotContext.setup_filters = setup_filters
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
    context.setup_middlewares()
    context.setup_filters()
    context.setup_handlers()
    context.run()
