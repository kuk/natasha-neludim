
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
from functools import partial

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


######
#  CHAT
#####


EDIT_NAME_STATE = 'edit_name'
EDIT_CITY_STATE = 'edit_city'
EDIT_LINKS_STATE = 'edit_links'
EDIT_ABOUT_STATE = 'edit_about'
CONTACT_FEEDBACK_STATE = 'contact_feedback'


@dataclass
class Chat:
    id: int
    state: str = None


####
#   USER
######


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

    agreed_participate: Datetime = None
    paused: Datetime = None
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


def find_user(users, username=None, user_id=None):
    for user in users:
        if (
            username and user.username == username
            or user_id and user.user_id == user_id
        ):
            return user


#######
#  CONTACT
######


CONFIRM_STATE = 'confirm'
FAIL_STATE = 'fail'


@dataclass
class Contact:
    week_index: int
    user_id: int
    partner_user_id: int

    state: str = None
    feedback: str = None

    @property
    def key(self):
        return (
            self.week_index,
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


CHATS_TABLE = 'chats'
CHATS_KEY = 'id'

USERS_TABLE = 'users'
USERS_KEY = 'user_id'

CONTACTS_TABLE = 'contacts'
CONTACTS_KEY = 'key'


async def put_chat(db, chat):
    item = dynamo_serialize_item(chat)
    await dynamo_put(db.client, CHATS_TABLE, item)


async def get_chat(db, id):
    item = await dynamo_get(
        db.client, CHATS_TABLE,
        CHATS_KEY, N, id
    )
    if not item:
        return
    return dynamo_deserialize_item(item, Chat)


async def set_chat_state(db, id, state):
    chat = Chat(id, state)
    await put_chat(db, chat)


async def get_chat_state(db, id):
    chat = await get_chat(db, id)
    if chat:
        return chat.state


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


DB.put_chat = put_chat
DB.get_chat = get_chat
DB.set_chat_state = set_chat_state
DB.get_chat_state = get_chat_state

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

SHOW_CONTACT_COMMAND = 'show_contact'
CONFIRM_CONTACT_COMMAND = 'confirm_contact'
FAIL_CONTACT_COMMAND = 'fail_contact'
CONTACT_FEEDBACK_COMMAND = 'contact_feedback'

COMMAND_DESCRIPTIONS = {
    START_COMMAND: 'инструкция, список команд',

    EDIT_INTRO_COMMAND: 'поменять анкету',
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


COMMANDS_TEXT = f'''{command_description(EDIT_INTRO_COMMAND)}
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


MONTHS = {
    1: 'января',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря',
}


def day_month(datetime):
    return f'{datetime.day} {MONTHS[datetime.month]}'


def day_day_month(start, stop):
    if start.month == stop.month:
        return f'{start.day}-{stop.day} {MONTHS[start.month]}'
    else:
        return f'{day_month(start)} - {day_month(stop)}'


def start_text(schedule):
    return f'''Бот организует random coffee для сообщества @natural_language_processing.

Инструкция:
1. Заполни короткую анкету /{EDIT_INTRO_COMMAND}.
2. Дай согласия на участие во встречах /{PARTICIPATE_COMMAND}. В понедельник {day_month(schedule.next_week_monday())} бот подберёт собеседника, пришлёт анкету и контакт.
3. Заходи в закрытый чат для первых участников https://t.me/+-A_Q6y-dODY3OTli. Там разработчик бота @alexkuk принимает баг репорты, рассказывает о новых фичах.

{COMMANDS_TEXT}'''


OTHER_TEXT = f'''Бот ответчает только на команды.

{COMMANDS_TEXT}'''


EMPTY_SYMBOL = '∅'


def intro_text(intro):
    return f'''Имя: {intro.name or EMPTY_SYMBOL}
Город: {intro.city or EMPTY_SYMBOL}
Ссылки: {intro.links or EMPTY_SYMBOL}
О себе: {intro.about or EMPTY_SYMBOL}'''


def edit_intro_text(intro):
    return f'''{intro_text(intro)}

{command_description(EDIT_NAME_COMMAND)}
{command_description(EDIT_CITY_COMMAND)}
{command_description(EDIT_LINKS_COMMAND)}
{command_description(EDIT_ABOUT_COMMAND)}

{command_description(CANCEL_COMMAND)}
{command_description(EMPTY_COMMAND)}'''


EDIT_NAME_TEXT = '''Напиши своё настоящее имя. Собеседник поймёт, как к тебе обращаться.'''

EDIT_CITY_TEXT = '''Напиши город, в котором живёшь. Собеседник поймет предлагать офлайн встречу или нет.'''

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


def participate_text(schedule):
    return f'Пометил, что участвуешь во встречах. В понедельник {day_month(schedule.next_week_monday())} бот подберёт собеседника, пришлёт анкету и контакт.'


PAUSE_TEXT = 'Поставил встречи на паузу. Бот не будет присылать контакты собеседников и напоминания.'


def no_contact_text(schedule):
    return f'Бот не назначил тебе собеседника. Бот составляет пары по понедельникам, очередной раунд {day_month(schedule.next_week_monday())}.'


def show_contact_text(user):
    return f'''Контакт собеседника в Телеграме: <a href="{user_url(user.user_id)}">{user_mention(user)}</a>.

{intro_text(user.intro)}

{command_description(CONFIRM_CONTACT_COMMAND)}
{command_description(FAIL_CONTACT_COMMAND)}
{command_description(CONTACT_FEEDBACK_COMMAND)}'''


CONFIRM_CONTACT_TEXT = f'Рад, что получилось договориться! Оставь фидбек после встречи /{CONTACT_FEEDBACK_COMMAND}.'


def fail_contact_text(schedule):
    return f'Жаль, что встреча не состоится. В понедельник {day_month(schedule.next_week_monday())} бот подберёт нового собеседника, пришлёт анкету и контакт.'


def contact_feedback_text(user):
    return f'''Собеседник: <a href="{user_url(user.user_id)}">{user_mention(user)}</a>

Оцени встречу:
1 - очень плохо
⋮
5 - очень хорошо

Или напиши фидбек своими словами.

{command_description(CANCEL_COMMAND)}
{command_description(EMPTY_COMMAND)}'''


CONTACT_FEEDBACK_OPTIONS = '12345'


def contact_feedback_state_text(user, contact):
    return f'Фидбек: "{contact.feedback or EMPTY_SYMBOL}"'


######
#  START
######


async def handle_start(context, message):
    user = await context.db.get_user(message.from_user.id)
    if not user:
        user = User(
            user_id=message.from_user.id,
            username=message.from_user.username,
            intro=Intro(
                name=message.from_user.full_name,
            )
        )
        await context.db.put_user(user)

    await context.bot.set_my_commands(commands=[
        BotCommand(command, description)
        for command, description
        in COMMAND_DESCRIPTIONS.items()
    ])

    text = start_text(context.schedule)
    await message.answer(text=text)


#####
#  INTRO
######


async def handle_edit_intro(context, message):
    user = await context.db.get_user(message.from_user.id)
    text = edit_intro_text(user.intro)
    await message.answer(text=text)


async def handle_edit_name(context, message):
    user = await context.db.get_user(message.from_user.id)

    markup = None
    if not user.intro.name and message.from_user.full_name:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(message.from_user.full_name)

    await message.answer(
        text=EDIT_NAME_TEXT,
        reply_markup=markup
    )
    await context.db.set_chat_state(
        message.chat.id,
        EDIT_NAME_STATE
    )


async def handle_edit_city(context, message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for city in TOP_CITIES:
        markup.insert(city)

    await message.answer(
        text=EDIT_CITY_TEXT,
        reply_markup=markup
    )
    await context.db.set_chat_state(
        message.chat.id,
        EDIT_CITY_STATE
    )


async def handle_edit_links(context, message):
    await message.answer(text=EDIT_LINKS_TEXT)
    await context.db.set_chat_state(
        message.chat.id,
        EDIT_LINKS_STATE
    )


async def handle_edit_about(context, message):
    await message.answer(text=EDIT_ABOUT_TEXT)
    await context.db.set_chat_state(
        message.chat.id,
        EDIT_ABOUT_STATE
    )


def parse_command(text):
    if text.startswith('/'):
        return text.lstrip('/')


async def handle_edit_intro_states(context, message):
    state = await context.db.get_chat_state(message.chat.id)
    user = await context.db.get_user(message.from_user.id)

    command = parse_command(message.text)
    if command != CANCEL_COMMAND:
        if command != EMPTY_COMMAND:
            value = message.text
        else:
            value = None

        if state == EDIT_NAME_STATE:
            user.intro.name = value
        elif state == EDIT_CITY_STATE:
            user.intro.city = value
        elif state == EDIT_LINKS_STATE:
            user.intro.links = value
        elif state == EDIT_ABOUT_STATE:
            user.intro.about = value

        await context.db.put_user(user)

    text = edit_intro_text(user.intro)
    await message.answer(
        text=text,
        reply_markup=ReplyKeyboardRemove()
    )
    await context.db.set_chat_state(
        message.chat.id,
        state=None
    )


######
#  PARTICIPATE/PAUSE
#######


async def handle_participate(context, message):
    user = await context.db.get_user(message.from_user.id)

    user.agreed_participate = context.schedule.now()
    user.paused = None
    user.pause_period = None

    await context.db.put_user(user)

    text = participate_text(context.schedule)
    await message.answer(text=text)


async def handle_pause(context, message):
    user = await context.db.get_user(message.from_user.id)

    user.agreed_participate = None
    user.paused = context.schedule.now()

    command = parse_command(message.text)
    if command == PAUSE_WEEK_COMMAND:
        user.pause_period = WEEK
    elif command == PAUSE_MONTH_COMMAND:
        user.pause_period = MONTH

    await context.db.put_user(user)
    await message.answer(text=PAUSE_TEXT)


######
#  CONTACT
#########


async def handle_contact(context, message):
    user = await context.db.get_user(message.from_user.id)

    if not user.partner_user_id:
        text = no_contact_text(context.schedule)
        await message.answer(text=text)
        return

    key = (
        context.schedule.now_week_index(),
        user.user_id,
        user.partner_user_id
    )
    contact = await context.db.get_contact(key)
    if not contact:
        text = no_contact_text(context.schedule)
        await message.answer(text=text)
        return

    contact.user = user
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

    text = fail_contact_text(context.schedule)
    await message.answer(text=text)


async def handle_contact_feedback(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=len(CONTACT_FEEDBACK_OPTIONS)
    )
    for option in CONTACT_FEEDBACK_OPTIONS:
        markup.insert(option)

    text = contact_feedback_text(contact.user)
    await message.answer(
        text=text,
        reply_markup=markup
    )
    await context.db.set_chat_state(
        message.chat.id,
        CONTACT_FEEDBACK_STATE
    )


async def handle_contact_feedback_state(context, message):
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

    text = contact_feedback_state_text(contact.user, contact)
    await message.answer(
        text=text,
        reply_markup=ReplyKeyboardRemove()
    )
    await context.db.set_chat_state(
        message.chat.id,
        state=None
    )


######
#  OTHER
########


async def handle_other(context, message):
    await message.answer(text=OTHER_TEXT)


#######
#   SETUP
######


def setup_handlers(context):
    context.dispatcher.register_message_handler(
        partial(handle_start, context),
        commands=START_COMMAND,
    )

    context.dispatcher.register_message_handler(
        partial(handle_edit_intro, context),
        commands=EDIT_INTRO_COMMAND
    )
    context.dispatcher.register_message_handler(
        partial(handle_edit_name, context),
        commands=EDIT_NAME_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_edit_city, context),
        commands=EDIT_CITY_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_edit_links, context),
        commands=EDIT_LINKS_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_edit_about, context),
        commands=EDIT_ABOUT_COMMAND,
    )

    context.dispatcher.register_message_handler(
        partial(handle_participate, context),
        commands=PARTICIPATE_COMMAND
    )
    context.dispatcher.register_message_handler(
        partial(handle_pause, context),
        commands=[
            PAUSE_WEEK_COMMAND,
            PAUSE_MONTH_COMMAND,
        ]
    )

    context.dispatcher.register_message_handler(
        partial(handle_show_contact, context),
        commands=SHOW_CONTACT_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_confirm_contact, context),
        commands=CONFIRM_CONTACT_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_fail_contact, context),
        commands=FAIL_CONTACT_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_contact_feedback, context),
        commands=CONTACT_FEEDBACK_COMMAND,
    )

    # Every call to chat_states filter = db query. Place handlers
    # last. TODO Implement aiogram storage adapter for DynamoDB,
    # natively handle FSM

    context.dispatcher.register_message_handler(
        partial(handle_edit_intro_states, context),
        chat_states=[
            EDIT_NAME_STATE,
            EDIT_CITY_STATE,
            EDIT_LINKS_STATE,
            EDIT_ABOUT_STATE,
        ]
    )
    context.dispatcher.register_message_handler(
        partial(handle_contact_feedback_state, context),
        chat_states=CONTACT_FEEDBACK_STATE,
    )

    context.dispatcher.register_message_handler(
        partial(handle_other, context)
    )


#####
#
#  FILTER
#
####


class ChatStatesFilter(BoundFilter):
    context = None
    key = 'chat_states'

    def __init__(self, chat_states):
        if not isinstance(chat_states, list):
            chat_states = [chat_states]
        self.chat_states = chat_states

    async def check(self, obj):
        state = await self.context.db.get_chat_state(obj.chat.id)
        return state in self.chat_states


def setup_filters(context):
    ChatStatesFilter.context = context
    context.dispatcher.filters_factory.bind(ChatStatesFilter)


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


def setup_middlewares(context):
    middlewares = [
        PrivateMiddleware(),
        LoggingMiddleware(),
    ]
    for middleware in middlewares:
        context.dispatcher.middleware.setup(middleware)


########
#
#   WEBHOOK
#
######


async def on_startup(context, _):
    await context.db.connect()


async def on_shutdown(context, _):
    await context.db.close()


PORT = getenv('PORT', 8080)


def start_bot_webhook(context):
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


########
#
#   CONTEXT
#
######


class Context:
    def __init__(self):
        self.bot = Bot(
            token=BOT_TOKEN,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        self.dispatcher = Dispatcher(self.bot)
        self.db = DB()
        self.schedule = Schedule()


######
#
#   SCHEDULE
#
####


START_DATE = Datetime.fromisoformat('2022-08-15')
START_DATE -= Timedelta(days=START_DATE.weekday())  # monday


def week_index(datetime):
    return (datetime - START_DATE).days // 7


def week_index_monday(index):
    return START_DATE + Timedelta(days=7 * index)


def monday_sunday(monday):
    return monday + Timedelta(days=6)


class Schedule:
    now = Datetime.utcnow

    def now_week_index(self):
        return week_index(self.now())

    def next_week_monday(self):
        next_week_index = self.now_week_index() + 1
        return week_index_monday(next_week_index)


######
#
#   MAIN
#
#####


def bot_main():
    context = Context()
    setup_middlewares(context)
    setup_filters(context)
    setup_handlers(context)
    start_bot_webhook(context)


if __name__ == '__main__':
    bot_main()
