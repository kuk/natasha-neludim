
from json import (
    loads as parse_json,
    dumps as format_json
)

from aiogram.types import Update

import pytest

from neludim.bot.bot import (
    Bot,
    Dispatcher,
    setup_bot,
)
from neludim.schedule import (
    Schedule,
    START_DATE,
)
from neludim.db import DB
from neludim.context import Context


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
        self.chat_states = {}
        self.users = []
        self.contacts = []

    async def set_chat_state(self, id, state):
        self.chat_states[id] = state

    async def get_chat_state(self, id):
        return self.chat_states.get(id)

    async def read_users(self):
        return self.users

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

    async def read_contacts(self):
        return self.contacts

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


class FakeSchedule(Schedule):
    def now(self):
        return START_DATE


class FakeContext(Context):
    def __init__(self):
        Context.__init__(self)
        self.bot = FakeBot()
        self.dispatcher = Dispatcher(self.bot)
        self.db = FakeDB()
        self.schedule = FakeSchedule()


@pytest.fixture(scope='function')
def context():
    context = FakeContext()
    setup_bot(context)

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

    for (method, json), (etalon_method, etalon_pattern) in zip(trace, etalon):
        if method != etalon_method:
            return False

        if etalon_pattern not in json:
            return False

    return True
