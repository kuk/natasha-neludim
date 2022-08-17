
import json
import logging
from os import getenv
from dataclasses import (
    dataclass,
    fields,
    is_dataclass,
)
from datetime import datetime as Datetime
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
EDIT_ABOUT_STATE = 'edit_about'

WEEK = 'week'
MONTH = 'month'


@dataclass
class Intro:
    name: str = None
    city: str = None
    links: str = None
    about: str = None


@dataclass
class User:
    user_id: int
    username: str = None
    state: str = None

    participate_date: Datetime = None
    pause_date: Datetime = None
    pause_period: str = None

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


async def dynamo_scan(client, table):
    response = await client.scan(
        TableName=table
    )
    return response['Items']


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
    elif annot in (str, Datetime):
        return S
    elif is_dataclass(annot):
        return M


def dynamo_parse_value(value, annot):
    if annot == int:
        return int(value)
    elif annot == str:
        return value
    elif annot == Datetime:
        return Datetime.fromisoformat(value)
    elif is_dataclass(annot):
        return dynamo_parse_item(value, annot)


def dynamo_format_value(value, annot):
    if annot == int:
        return str(value)
    elif annot == str:
        return value
    elif annot == Datetime:
        return value.isoformat()
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


async def read_users(db):
    items = await dynamo_scan(db.client, USERS_TABLE)
    return [dynamo_parse_item(_, User) for _ in items]


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


DB.read_users = read_users
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
EDIT_ABOUT_COMMAND = 'edit_about'

CANCEL_COMMAND = 'cancel'
EMPTY_COMMAND = 'empty'

PARTICIPATE_COMMAND = 'participate'
PAUSE_WEEK_COMMAND = 'pause_week'
PAUSE_MONTH_COMMAND = 'pause_month'

CONFIRM_PAIR_COMMAND = 'confirm_pair'
BREAK_PAIR_COMMAND = 'break_pair'
PAIR_FEEDBACK_COMMAND = 'pair_feedback'

COMMAND_DESCRIPTIONS = {
    START_COMMAND: 'интро + список команд',

    EDIT_INTRO_COMMAND: 'поменять анкету',
    EDIT_NAME_COMMAND: 'поменять имя',
    EDIT_CITY_COMMAND: 'поменять город',
    EDIT_LINKS_COMMAND: 'поменять ссылки',
    EDIT_ABOUT_COMMAND: 'поменять "о себе"',

    CANCEL_COMMAND: 'отменить',
    EMPTY_COMMAND: 'оставить пустым',

    PARTICIPATE_COMMAND: 'участвовать во встречах',
    PAUSE_WEEK_COMMAND: 'пауза на неделю',
    PAUSE_MONTH_COMMAND: 'пауза на месяц',

    CONFIRM_PAIR_COMMAND: 'договорились о встрече',
    BREAK_PAIR_COMMAND: 'не договориль/не отвечает',
    PAIR_FEEDBACK_COMMAND: 'как прошла встреча',
}


#####
#  TEXT
####


def command_description(command):
    return f'/{command} — {COMMAND_DESCRIPTIONS[command]}'


START_TEXT = f'''Бот организует random coffee для сообщества @natural_language_processing.

Встречи начнутся в понедельник 22 августа. Пока заполни, пожалуйста, короткую анкету /{EDIT_INTRO_COMMAND}. Заходи в закрытый чат для первых участников https://t.me/+cNnNahFlZ_gzZDYy.

{command_description(EDIT_INTRO_COMMAND)}
{command_description(EDIT_NAME_COMMAND)}
{command_description(EDIT_CITY_COMMAND)}
{command_description(EDIT_LINKS_COMMAND)}
{command_description(EDIT_ABOUT_COMMAND)}

{command_description(PARTICIPATE_COMMAND)}
{command_description(PAUSE_WEEK_COMMAND)}
{command_description(PAUSE_MONTH_COMMAND)}

{command_description(CONFIRM_PAIR_COMMAND)}
{command_description(BREAK_PAIR_COMMAND)}
{command_description(PAIR_FEEDBACK_COMMAND)}

{command_description(START_COMMAND)}
'''


def format_empty(value):
    if value is None:
        return '∅'
    return value


EDIT_INTRO_TEXT = f'''Имя: {{name}}
Город: {{city}}
Ссылки: {{links}}
О себе: {{about}}

{command_description(EDIT_NAME_COMMAND)}
{command_description(EDIT_CITY_COMMAND)}
{command_description(EDIT_LINKS_COMMAND)}
{command_description(EDIT_ABOUT_COMMAND)}

{command_description(CANCEL_COMMAND)}
{command_description(EMPTY_COMMAND)}
'''

EDIT_NAME_TEXT = '''Напиши настоящее имя. Собеседник поймёт, как к тебе обращаться.'''

EDIT_CITY_TEXT = '''Напиши город, в котором живёшь. Собеседник поймет предлагать оффлайн встречу или нет.'''

EDIT_LINKS_TEXT = '''Накидай ссылок про себя: блог, твиттер, фейсбук, канал, подкаст. Собеседник поймёт чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.

Примеры
- http://lab.alexkuk.ru, https://github.com/kuk, https://habr.com/ru/users/alexanderkuk/
- https://www.linkedin.com/in/alexkuk/, https://vk.com/alexkuk
- http://val.maly.hk'''

EDIT_ABOUT_TEXT = '''Напиши о себе. Собеседник поймёт чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.

Что писать?
- Где учился?
- Где успел поработать? Чем занимался, самое важное/удивительное?
- Сфера интересов в NLP?
- Личное, чем занимаешь кроме работы?

Например
"Закончил ШАД, работал в Яндексе в поиске. Сделал библиотеку Nile, чтобы удобно ворочать логи на Мап Редьюсе https://habr.com/ru/company/yandex/blog/332688/.

Автор проекта Наташа https://github.com/natasha. Работаю в своей Лабе https://lab.alexkuk.ru, адаптирую Наташу под задачи клиентов.

Живу в Москве в Крылатском. У нас тут мекка велоспорта. Умею сидеть на колесе и сдавать смену. Вожу экскурсии. Могу рассказать про путь от академизма к супрематизму."'''

TOP_CITIES = [
    'Москва',
    'Санкт-Петербург',
    'Киев',
    'Минск',
    'Лондон',
    'Берлин',
]

PARTICIPATE_TEXT = 'Бот подберёт пару, пришлёт контакт собеседника.'

PAUSE_TEXT = 'Поставил встречи на паузу. Бот не будет тебя беспокоить.'

PAIR_STUB_TEXT = 'Бот ещё не подобрал тебе пару.'


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
        links=format_empty(user.intro.links),
        about=format_empty(user.intro.about)
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


async def handle_edit_about(context, message):
    user = context.user.get()
    user.state = EDIT_ABOUT_STATE

    await message.answer(text=EDIT_ABOUT_TEXT)


def parse_command(text):
    if text.startswith('/'):
        return text.lstrip('/')


async def handle_edit_states(context, message):
    user = context.user.get()

    command = parse_command(message.text)
    if command != CANCEL_COMMAND:
        if command != EMPTY_COMMAND:
            value = message.text
        else:
            value = None

        if user.state == EDIT_NAME_STATE:
            user.intro.name = value
        elif user.state == EDIT_CITY_STATE:
            user.intro.city = value
        elif user.state == EDIT_LINKS_STATE:
            user.intro.links = value
        elif user.state == EDIT_ABOUT_STATE:
            user.intro.about = value

    user.state = None
    text = format_edit_intro_text(user)
    await message.answer(
        text=text,
        reply_markup=ReplyKeyboardRemove()
    )


######
#  PARTICIPATE/PAUSE
#######


async def handle_participate(context, message):
    user = context.user.get()
    user.participate_date = context.now()
    user.pause_date = None
    user.pause_period = None

    await message.answer(text=PARTICIPATE_TEXT)


async def handle_pause(context, message):
    user = context.user.get()

    user.participate_date = None
    user.pause_date = context.now()

    command = parse_command(message.text)
    if command == PAUSE_WEEK_COMMAND:
        user.pause_period = WEEK
    elif command == PAUSE_MONTH_COMMAND:
        user.pause_period = MONTH

    await message.answer(text=PAUSE_TEXT)


######
#  OTHER/STUB
########


async def handle_other(context, message):
    await message.answer(text=START_TEXT)


async def handle_stub(context, message):
    await message.answer(text=PAIR_STUB_TEXT)


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
        context.handle_edit_about,
        commands=EDIT_ABOUT_COMMAND,
    )
    context.dispatcher.register_message_handler(
        context.handle_edit_states,
        user_states=[
            EDIT_NAME_STATE,
            EDIT_CITY_STATE,
            EDIT_LINKS_STATE,
            EDIT_ABOUT_STATE,
        ]
    )

    context.dispatcher.register_message_handler(
        context.handle_participate,
        commands=PARTICIPATE_COMMAND
    )
    context.dispatcher.register_message_handler(
        context.handle_pause,
        commands=[
            PAUSE_WEEK_COMMAND,
            PAUSE_MONTH_COMMAND,
        ]
    )

    context.dispatcher.register_message_handler(
        context.handle_stub,
        commands=[
            CONFIRM_PAIR_COMMAND,
            BREAK_PAIR_COMMAND,
            PAIR_FEEDBACK_COMMAND,
        ]
    )
    context.dispatcher.register_message_handler(
        context.handle_other
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

    def now(self):
        return Datetime.now()


BotContext.handle_start = handle_start
BotContext.handle_edit_intro = handle_edit_intro
BotContext.handle_edit_name = handle_edit_name
BotContext.handle_edit_city = handle_edit_city
BotContext.handle_edit_links = handle_edit_links
BotContext.handle_edit_about = handle_edit_about
BotContext.handle_edit_states = handle_edit_states
BotContext.handle_participate = handle_participate
BotContext.handle_pause = handle_pause
BotContext.handle_stub = handle_stub
BotContext.handle_other = handle_other

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
