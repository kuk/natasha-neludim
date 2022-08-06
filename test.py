
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

    User
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
        intro='abc'
    )

    await db.put_user(user)
    assert user == await db.get_user(user_id=user.user_id)

    await db.delete_user(user_id=user.user_id)
    assert await db.get_user(user_id=user.user_id) is None


#######
#
#  BOT
#
######


class FakeBot(Bot):
    def __init__(self, token):
        Bot.__init__(self, token)
        self.trace = []

    async def request(self, method, data):
        json = format_json(data, ensure_ascii=False)
        self.trace.append([method, json])
        return {}


class FakeDB(DB):
    def __init__(self):
        DB.__init__(self)
        self.users = []

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


class FakeBotContext(BotContext):
    def __init__(self):
        self.bot = FakeBot('123:faketoken')
        self.dispatcher = Dispatcher(self.bot)
        self.db = FakeDB()



@pytest.fixture(scope='function')
def context():
    context = FakeBotContext()
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


START_JSON = '{"message": {"message_id": 2, "from": {"id": 113947584, "is_bot": false, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "language_code": "ru"}, "chat": {"id": 113947584, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "type": "private"}, "date": 1659800990, "text": "/start", "entities": [{"type": "bot_command", "offset": 0, "length": 6}]}}'


async def test_bot_start(context):
    await process_update(context, START_JSON)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "<b>Что это?</b>']
    ])
