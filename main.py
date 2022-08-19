
import json
import logging
from os import getenv
from dataclasses import (
    dataclass,
    fields,
    is_dataclass,
)
from datetime import (
    datetime as Datetime,
    timedelta as Timedelta
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

FEEDBACK_STATE = 'feedback'

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

    partner_user_id: int = None


def user_mention(user):
    if user.username:
        return f'@{user.username}'
    elif user.intro.name:
        return user.intro.name
    return user.user_id


def user_url(user_id):
    return f'tg://user?id={user_id}'


#######
#  CONTACT
######


CONFIRM_STATE = 'confirm'
FAIL_STATE = 'fail'


@dataclass
class Contact:
    week_id: int
    user_id: int
    partner_user_id: int

    state: str = None
    feedback: str = None

    @property
    def key(self):
        return (
            self.week_id,
            self.user_id,
            self.partner_user_id
        )


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


BOOL = 'BOOL'
N = 'N'
S = 'S'
M = 'M'


def dynamo_type(annot):
    if annot == bool:
        return BOOL
    elif annot == int:
        return N
    elif annot in (str, Datetime):
        return S
    elif is_dataclass(annot):
        return M


def dynamo_deserialize_value(value, annot):
    if annot == bool:
        return value
    elif annot == int:
        return int(value)
    elif annot == str:
        return value
    elif annot == Datetime:
        return Datetime.fromisoformat(value)
    elif is_dataclass(annot):
        return dynamo_deserialize_item(value, annot)


def dynamo_serialize_value(value, annot):
    if annot == bool:
        return value
    elif annot == int:
        return str(value)
    elif annot == str:
        return value
    elif annot == Datetime:
        return value.isoformat()
    elif is_dataclass(annot):
        return dynamo_serialize_item(value)


def dynamo_deserialize_item(item, cls):
    kwargs = {}
    for name, annot in obj_annots(cls):
        if name in item:
            type = dynamo_type(annot)
            value = item[name][type]
            value = dynamo_deserialize_value(value, annot)
        else:
            value = None
        kwargs[name] = value
    return cls(**kwargs)


def dynamo_serialize_item(obj):
    item = {}
    for name, annot in obj_annots(obj):
        value = getattr(obj, name)
        if value is not None:
            value = dynamo_serialize_value(value, annot)
            type = dynamo_type(annot)
            item[name] = {type: value}
    return item


#####
#  KEY
######


# On DynamoDB partition key
# https://aws.amazon.com/ru/blogs/database/choosing-the-right-dynamodb-partition-key/


def dynamo_key(parts):
    return '#'.join(
        str(_) for _ in parts
    )


######
#   READ/WRITE
######


USERS_TABLE = 'users'
USERS_KEY = 'user_id'

CONTACTS_TABLE = 'contacts'
CONTACTS_KEY = 'key'


async def read_users(db):
    items = await dynamo_scan(db.client, USERS_TABLE)
    return [dynamo_deserialize_item(_, User) for _ in items]


async def put_user(db, user):
    item = dynamo_serialize_item(user)
    await dynamo_put(db.client, USERS_TABLE, item)


async def get_user(db, user_id):
    item = await dynamo_get(
        db.client, USERS_TABLE,
        USERS_KEY, N, user_id
    )
    if not item:
        return
    return dynamo_deserialize_item(item, User)


async def delete_user(db, user_id):
    await dynamo_delete(
        db.client, USERS_TABLE,
        USERS_KEY, N, user_id
    )


async def read_contacts(db):
    items = await dynamo_scan(db.client, CONTACTS_TABLE)
    return [dynamo_deserialize_item(_, Contact) for _ in items]


async def put_contact(db, contact):
    item = dynamo_serialize_item(contact)
    item[CONTACTS_KEY] = {S: dynamo_key(contact.key)}
    await dynamo_put(db.client, CONTACTS_TABLE, item)


async def get_contact(db, key):
    item = await dynamo_get(
        db.client, CONTACTS_TABLE,
        CONTACTS_KEY, S, dynamo_key(key)
    )
    if not item:
        return
    return dynamo_deserialize_item(item, Contact)


async def delete_contact(db, key):
    await dynamo_delete(
        db.client, CONTACTS_TABLE,
        CONTACTS_KEY, S, dynamo_key(key)
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

DB.read_contacts = read_contacts
DB.put_contact = put_contact
DB.get_contact = get_contact
DB.delete_contact = delete_contact


#####
#
#  HANDLERS
#
#####


######
#   COMMAND
######


START_COMMAND = 'start'

SHOW_INTRO_COMMAND = 'show_intro'
EDIT_NAME_COMMAND = 'edit_name'
EDIT_CITY_COMMAND = 'edit_city'
EDIT_LINKS_COMMAND = 'edit_links'
EDIT_ABOUT_COMMAND = 'edit_about'

CANCEL_COMMAND = 'cancel'
EMPTY_COMMAND = 'empty'

PARTICIPATE_COMMAND = 'participate'
PAUSE_WEEK_COMMAND = 'pause_week'
PAUSE_MONTH_COMMAND = 'pause_month'

SHOW_CONTACT_COMMAND = 'show_contact'
CONFIRM_CONTACT_COMMAND = 'confirm_contact'
FAIL_CONTACT_COMMAND = 'fail_contact'
CONTACT_FEEDBACK_COMMAND = 'contact_feedback'

COMMAND_DESCRIPTIONS = {
    START_COMMAND: 'список команд',

    SHOW_INTRO_COMMAND: 'моя анкета',
    EDIT_NAME_COMMAND: 'поменять имя',
    EDIT_CITY_COMMAND: 'поменять город',
    EDIT_LINKS_COMMAND: 'поменять ссылки',
    EDIT_ABOUT_COMMAND: 'поменять "о себе"',

    PARTICIPATE_COMMAND: 'участвовать во встречах',
    PAUSE_WEEK_COMMAND: 'пауза на неделю',
    PAUSE_MONTH_COMMAND: 'пауза на месяц',

    SHOW_CONTACT_COMMAND: 'контакт, анкета собеседника',
    CONFIRM_CONTACT_COMMAND: 'договорились о встрече',
    FAIL_CONTACT_COMMAND: 'не договорились/не отвечает',
    CONTACT_FEEDBACK_COMMAND: 'как прошла встреча',

    CANCEL_COMMAND: 'отменить',
    EMPTY_COMMAND: 'оставить пустым',
}


#####
#  TEXT
####


def command_description(command):
    return f'/{command} - {COMMAND_DESCRIPTIONS[command]}'


START_TEXT = f'''Бот организует random coffee для сообщества @natural_language_processing.

Заполни, пожалуйста, короткую анкету /{SHOW_INTRO_COMMAND}. Заходи в закрытый чат для первых участников https://t.me/+cNnNahFlZ_gzZDYy.

{command_description(SHOW_INTRO_COMMAND)}
{command_description(EDIT_NAME_COMMAND)}
{command_description(EDIT_CITY_COMMAND)}
{command_description(EDIT_LINKS_COMMAND)}
{command_description(EDIT_ABOUT_COMMAND)}

{command_description(PARTICIPATE_COMMAND)}
{command_description(PAUSE_WEEK_COMMAND)}
{command_description(PAUSE_MONTH_COMMAND)}

{command_description(SHOW_CONTACT_COMMAND)}
{command_description(CONFIRM_CONTACT_COMMAND)}
{command_description(FAIL_CONTACT_COMMAND)}
{command_description(CONTACT_FEEDBACK_COMMAND)}

{command_description(START_COMMAND)}'''


EMPTY_SYMBOL = '∅'


def intro_text(intro):
    return f'''Имя: {intro.name or EMPTY_SYMBOL}
Город: {intro.city or EMPTY_SYMBOL}
Ссылки: {intro.links or EMPTY_SYMBOL}
О себе: {intro.about or EMPTY_SYMBOL}'''


def show_intro_text(intro):
    return f'''{intro_text(intro)}

{command_description(EDIT_NAME_COMMAND)}
{command_description(EDIT_CITY_COMMAND)}
{command_description(EDIT_LINKS_COMMAND)}
{command_description(EDIT_ABOUT_COMMAND)}

{command_description(CANCEL_COMMAND)}
{command_description(EMPTY_COMMAND)}'''


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
- Сфера интересов в NLP? Проекты, статьи.
- Личное, чем занимаешься кроме работы? Спорт, игры. Где успел пожить?

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

PARTICIPATE_TEXT = 'Ура! Бот подберёт собеседника, пришлёт анкету и контакт.'
PAUSE_TEXT = 'Поставил встречи на паузу. Бот не будет присылать контакты собеседников и напоминания.'

NO_CONTACT_TEXT = 'Бот ещё не назначил тебе собеседника.'


def show_contact_text(user):
    return f'''Контакт собеседника в Телеграме: <a href="{user_url(user.user_id)}">{user_mention(user)}</a>.

{intro_text(user.intro)}

{command_description(CONFIRM_CONTACT_COMMAND)}
{command_description(FAIL_CONTACT_COMMAND)}
{command_description(CONTACT_FEEDBACK_COMMAND)}'''


CONFIRM_CONTACT_TEXT = f'Ура! Оставь фидбек после встречи /{CONTACT_FEEDBACK_COMMAND}.'
FAIL_CONTACT_TEXT = 'Эх, бот подберёт нового собеседника, пришлёт анкету и контакт.'

DISLIKE_FEEDBACK = '👎'
OK_FEEDBACK = '👌'
CONFUSED_FEEDBACK = '🤔'

FEEDBACK_TEXT = f'''Если вернуться назад во времени:
{DISLIKE_FEEDBACK} - предпочёл бы другого собеседника,
{OK_FEEDBACK} - ничего бы не менял,
{CONFUSED_FEEDBACK} - не знаю.

Или напиши фидбек своими словами.

{command_description(CANCEL_COMMAND)}
{command_description(EMPTY_COMMAND)}'''

ACK_FEEDBACK_TEXT = 'Спасибо! Принял фидбек.'


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


async def handle_show_intro(context, message):
    user = context.user.get()
    text = show_intro_text(user.intro)
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
        markup.insert(city)

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

    text = show_intro_text(user.intro)
    await message.answer(
        text=text,
        reply_markup=ReplyKeyboardRemove()
    )


######
#  PARTICIPATE/PAUSE
#######


async def handle_participate(context, message):
    user = context.user.get()

    user.participate_date = context.now.datetime()
    user.pause_date = None
    user.pause_period = None

    await message.answer(text=PARTICIPATE_TEXT)


async def handle_pause(context, message):
    user = context.user.get()

    user.participate_date = None
    user.pause_date = context.now.datetime()

    command = parse_command(message.text)
    if command == PAUSE_WEEK_COMMAND:
        user.pause_period = WEEK
    elif command == PAUSE_MONTH_COMMAND:
        user.pause_period = MONTH

    await message.answer(text=PAUSE_TEXT)


######
#  CONTACT
#########


async def handle_contact(context, message):
    user = context.user.get()

    if not user.partner_user_id:
        await message.answer(text=NO_CONTACT_TEXT)
        return

    key = (
        context.now.week_id(),
        user.user_id,
        user.partner_user_id
    )
    contact = await context.db.get_contact(key)
    if not contact:
        await message.answer(text=NO_CONTACT_TEXT)
        return

    return contact


async def handle_show_contact(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    partner_user = await context.db.get_user(contact.partner_user_id)
    text = show_contact_text(partner_user)
    await message.answer(text=text)


async def handle_confirm_contact(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    contact.state = CONFIRM_STATE
    await context.db.put_contact(contact)

    await message.answer(text=CONFIRM_CONTACT_TEXT)


async def handle_fail_contact(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    contact.state = FAIL_STATE
    await context.db.put_contact(contact)

    await message.answer(text=FAIL_CONTACT_TEXT)


async def handle_contact_feedback(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    user = context.user.get()
    user.state = FEEDBACK_STATE

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for feedback in [DISLIKE_FEEDBACK, OK_FEEDBACK, CONFUSED_FEEDBACK]:
        markup.insert(feedback)

    await message.answer(
        text=FEEDBACK_TEXT,
        reply_markup=markup
    )


async def handle_feedback_state(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    command = parse_command(message.text)
    if command != CANCEL_COMMAND:
        if command != EMPTY_COMMAND:
            contact.feedback = message.text
        else:
            contact.feedback = None
    await context.db.put_contact(contact)

    user = context.user.get()
    user.state = None

    await message.answer(
        text=ACK_FEEDBACK_TEXT,
        reply_markup=ReplyKeyboardRemove()
    )


######
#  OTHER
########


async def handle_other(context, message):
    await message.answer(text=START_TEXT)


#######
#   SETUP
######


def setup_handlers(context):
    context.dispatcher.register_message_handler(
        context.handle_start,
        commands=START_COMMAND,
    )

    context.dispatcher.register_message_handler(
        context.handle_show_intro,
        commands=SHOW_INTRO_COMMAND
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
        context.handle_show_contact,
        commands=SHOW_CONTACT_COMMAND,
    )
    context.dispatcher.register_message_handler(
        context.handle_confirm_contact,
        commands=CONFIRM_CONTACT_COMMAND,
    )
    context.dispatcher.register_message_handler(
        context.handle_fail_contact,
        commands=FAIL_CONTACT_COMMAND,
    )

    context.dispatcher.register_message_handler(
        context.handle_contact_feedback,
        commands=CONTACT_FEEDBACK_COMMAND,
    )
    context.dispatcher.register_message_handler(
        context.handle_feedback_state,
        user_states=FEEDBACK_STATE,
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
        if not isinstance(user_states, list):
            user_states = [user_states]
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
        self.now = Now()

        self.user = ContextVar(USER_VAR)


BotContext.handle_start = handle_start
BotContext.handle_show_intro = handle_show_intro
BotContext.handle_edit_name = handle_edit_name
BotContext.handle_edit_city = handle_edit_city
BotContext.handle_edit_links = handle_edit_links
BotContext.handle_edit_about = handle_edit_about
BotContext.handle_edit_states = handle_edit_states

BotContext.handle_participate = handle_participate
BotContext.handle_pause = handle_pause

BotContext.handle_show_contact = handle_show_contact
BotContext.handle_confirm_contact = handle_confirm_contact
BotContext.handle_fail_contact = handle_fail_contact

BotContext.handle_contact_feedback = handle_contact_feedback
BotContext.handle_feedback_state = handle_feedback_state

BotContext.handle_other = handle_other

BotContext.setup_middlewares = setup_middlewares
BotContext.setup_filters = setup_filters
BotContext.setup_handlers = setup_handlers

BotContext.on_startup = on_startup
BotContext.on_shutdown = on_shutdown
BotContext.run = run


######
#
#   TIME
#
####


START_DATE = Datetime.fromisoformat('2022-08-15')
START_DATE -= Timedelta(days=START_DATE.weekday())  # monday


def week_id(datetime):
    return (datetime - START_DATE).days // 7


now = Datetime.utcnow


class Now:
    datetime = now

    def week_id(self):
        return week_id(self.datetime())


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
