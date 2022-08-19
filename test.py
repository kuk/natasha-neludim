
import asyncio
from json import (
    loads as parse_json,
    dumps as format_json
)

import pytest

from aiogram.types import Update

from main import (
    Bot,
    Dispatcher,

    DB,
    BotContext,

    Now,
    START_DATE,

    User,
    Intro,
    MONTH,

    Contact,
    OK_FEEDBACK,
    CONFIRM_STATE,
    FAIL_STATE,
)


######
#
#   DB
#
#####


@pytest.fixture(scope='session')
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope='session')
async def db():
    db = DB()
    await db.connect()
    yield db
    await db.close()


async def test_db_user(db):
    user = User(
        user_id=1,
        intro=Intro(
            name='abc'
        )
    )

    await db.put_user(user)
    assert user == await db.get_user(user_id=user.user_id)

    await db.delete_user(user_id=user.user_id)
    assert await db.get_user(user_id=user.user_id) is None
    

async def test_db_contact(db):
    contact = Contact(
        week_id=0,
        user_id=1,
        partner_user_id=2
    )

    await db.put_contact(contact)
    assert contact == await db.get_contact(contact.key)

    await db.delete_contact(contact.key)
    assert await db.get_contact(contact.key) is None



#######
#
#  BOT
#
######


class FakeBot(Bot):
    def __init__(self):
        Bot.__init__(self, '123:faketoken')
        self.trace = []

    async def request(self, method, data):
        json = format_json(data, ensure_ascii=False)
        self.trace.append([method, json])
        return {}


class FakeDB(DB):
    def __init__(self):
        DB.__init__(self)
        self.users = []
        self.contacts = []

    async def put_user(self, user):
        await self.delete_user(user.user_id)
        self.users.append(user)

    async def get_user(self, user_id):
        for user in self.users:
            if user.user_id == user_id:
                return user

    async def delete_user(self, user_id):
        self.users = [
            _ for _ in self.users
            if _.user_id != user_id
        ]

    async def put_contact(self, contact):
        await self.delete_contact(contact.key)
        self.contacts.append(contact)

    async def get_contact(self, key):
        for contact in self.contacts:
            if contact.key == key:
                return contact

    async def delete_contact(self, key):
        self.contacts = [
            _ for _ in self.contacts
            if _.key != key
        ]


class FakeNow(Now):
    def datetime(self):
        return START_DATE


class FakeBotContext(BotContext):
    def __init__(self):
        BotContext.__init__(self)
        self.bot = FakeBot()
        self.dispatcher = Dispatcher(self.bot)
        self.db = FakeDB()
        self.now = FakeNow()


@pytest.fixture(scope='function')
def context():
    context = FakeBotContext()
    context.setup_middlewares()
    context.setup_filters()
    context.setup_handlers()

    Bot.set_current(context.bot)
    Dispatcher.set_current(context.dispatcher)

    return context


async def process_update(context, json):
    data = parse_json(json)
    update = Update(**data)
    await context.dispatcher.process_update(update)


def match_trace(trace, etalon):
    if len(trace) != len(etalon):
        return False

    for (method, json), (etalon_method, etalon_match) in zip(trace, etalon):
        if method != etalon_method:
            return False

        if etalon_match not in json:
            return False

    return True


######
#  START
######


START_JSON = '{"message": {"message_id": 2, "from": {"id": 113947584, "is_bot": false, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "language_code": "ru"}, "chat": {"id": 113947584, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "type": "private"}, "date": 1659800990, "text": "/start", "entities": [{"type": "bot_command", "offset": 0, "length": 6}]}}'


async def test_bot_start(context):
    await process_update(context, START_JSON)
    assert match_trace(context.bot.trace, [
        ['setMyCommands', '{"commands"'],
        ['sendMessage', '{"chat_id": 113947584, "text": "Бот организует']
    ])
    assert context.db.users == [User(user_id=113947584, username='alexkuk', intro=Intro(name='Alexander Kukushkin'))]


#######
#  INTRO
######


async def test_bot_edit_name(context):
    context.db.users = [User(user_id=113947584, intro=Intro())]
    await process_update(context, START_JSON.replace('/start', '/show_intro'))
    await process_update(context, START_JSON.replace('/start', '/edit_name'))
    await process_update(context, START_JSON.replace('/start', 'Alexander Kukushkin'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Имя:'],
        ['sendMessage', '{"chat_id": 113947584, "text": "Напиши настоящее имя'],
        ['sendMessage', '{"chat_id": 113947584, "text": "Имя: Alexander Kukushkin'],
    ])
    assert context.db.users[0].intro.name == 'Alexander Kukushkin'


async def test_bot_edit_city(context):
    context.db.users = [User(user_id=113947584, intro=Intro())]
    await process_update(context, START_JSON.replace('/start', '/edit_city'))
    await process_update(context, START_JSON.replace('/start', 'Moscow'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Напиши город'],
        ['sendMessage', 'Город: Moscow'],
    ])
    assert context.db.users[0].intro.city == 'Moscow'


async def test_bot_edit_links(context):
    context.db.users = [User(user_id=113947584, intro=Intro())]
    await process_update(context, START_JSON.replace('/start', '/edit_links'))
    await process_update(context, START_JSON.replace('/start', 'vk.com/alexkuk'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Накидай ссылок'],
        ['sendMessage', 'Ссылки: vk.com/alexkuk'],
    ])
    assert context.db.users[0].intro.links == 'vk.com/alexkuk'


async def test_bot_edit_about(context):
    context.db.users = [User(user_id=113947584, intro=Intro())]
    await process_update(context, START_JSON.replace('/start', '/edit_about'))
    await process_update(context, START_JSON.replace('/start', 'Закончил ШАД, работал в Яндексе'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Напиши о себе'],
        ['sendMessage', 'Закончил ШАД, работал в Яндексе'],
    ])
    assert context.db.users[0].intro.about == 'Закончил ШАД, работал в Яндексе'


async def test_bot_empty_edit(context):
    context.db.users = [User(user_id=113947584, intro=Intro(name='A K'))]
    await process_update(context, START_JSON.replace('/start', '/edit_name'))
    await process_update(context, START_JSON.replace('/start', '/empty'))
    assert context.db.users[0].intro.name is None


async def test_bot_cancel_edit(context):
    context.db.users = [User(user_id=113947584, intro=Intro(name='A K', links='vk.com/alexkuk'))]
    await process_update(context, START_JSON.replace('/start', '/edit_links'))
    await process_update(context, START_JSON.replace('/start', '/cancel'))

    assert context.db.users == [User(user_id=113947584, intro=Intro(name='A K', links='vk.com/alexkuk'))]


#######
#   PARTICIPATE/PAUSE
#######


async def test_bot_participate(context):
    context.db.users = [User(user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/participate'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Бот подберёт'],
    ])

    user = context.db.users[0]
    assert user.participate_date == context.now.datetime()
    assert user.pause_date is None


async def test_bot_pause(context):
    context.db.users = [User(user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/pause_month'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Поставил встречи на паузу'],
    ])

    user = context.db.users[0]
    assert user.participate_date is None
    assert user.pause_date == context.now.datetime()
    assert user.pause_period == MONTH


#######
#  CONTACT
######


async def test_bot_show_no_contact(context):
    context.db.users = [User(user_id=113947584, partner_user_id=None)]
    await process_update(context, START_JSON.replace('/start', '/show_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Бот ещё не назначил'],
    ])


async def test_bot_show_contact(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584, intro=Intro())]
    context.db.contacts = [Contact(week_id=0, user_id=113947584, partner_user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/show_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Контакт собеседника'],
    ])


async def test_bot_confirm_contact(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584)]
    context.db.contacts = [Contact(week_id=0, user_id=113947584, partner_user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/confirm_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Ура'],
    ])
    assert context.db.contacts[0].state == CONFIRM_STATE


async def test_bot_fail_contact(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584)]
    context.db.contacts = [Contact(week_id=0, user_id=113947584, partner_user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/fail_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Эх'],
    ])
    assert context.db.contacts[0].state == FAIL_STATE


async def test_bot_contact_feedback(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584, intro=Intro())]
    context.db.contacts = [Contact(week_id=0, user_id=113947584, partner_user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/contact_feedback'))
    await process_update(context, START_JSON.replace('/start', OK_FEEDBACK))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Если вернуться назад'],
        ['sendMessage', 'Фидбек'],
    ])
    assert context.db.contacts[0].feedback == OK_FEEDBACK


#######
#   OTHER/STUB
#######


async def test_bot_other(context):
    await process_update(context, START_JSON.replace('/start', 'abc'))
    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Бот организует']
    ])
