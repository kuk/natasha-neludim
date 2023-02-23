
from json import (
    loads as parse_json,
    dumps as format_json
)

from aiogram.types import Update

from neludim.bot.bot import (
    Bot,
    Dispatcher,
    setup_bot,
)
from neludim.bot.broadcast import Broadcast
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

    async def request(self, method, data, files=None):
        json = format_json(data, ensure_ascii=False)
        self.trace.append([method, json])
        return {}


class FakeDB(DB):
    def __init__(self):
        DB.__init__(self)
        self.chat_states = {}
        self.users = []
        self.contacts = []
        self.manual_matches = []

    async def connect(self):
        pass

    async def close(self):
        pass

    async def set_chat_state(self, id, state):
        self.chat_states[id] = state

    async def reset_chat_state(self, id):
        await self.set_chat_state(id, state=None)

    async def get_chat_state(self, id):
        return self.chat_states.get(id)

    async def get_user(self, user_id):
        for user in self.users:
            if user.user_id == user_id:
                return user

    async def read_users(self):
        return self.users

    async def put_user(self, user):
        await self.delete_user(user.user_id)
        self.users.append(user)

    async def delete_user(self, user_id):
        self.users = [
            _ for _ in self.users
            if _.user_id != user_id
        ]

    async def put_users(self, users):
        for user in users:
            await self.put_user(user)

    async def delete_users(self, users):
        for user in users:
            await self.delete_user(user)

    async def get_contact(self, key):
        for contact in self.contacts:
            if contact.key == key:
                return contact

    async def read_contacts(self):
        return self.contacts

    async def put_contact(self, contact):
        await self.delete_contact(contact.key)
        self.contacts.append(contact)

    async def delete_contact(self, key):
        self.contacts = [
            _ for _ in self.contacts
            if _.key != key
        ]

    async def put_contacts(self, contacts):
        for contact in contacts:
            await self.put_contact(contact)

    async def delete_contacts(self, contacts):
        for contact in contacts:
            await self.delete_contact(contact)

    async def read_manual_matches(self):
        return self.manual_matches

    async def put_manual_match(self, match):
        await self.delete_manual_match(match.key)
        self.manual_matches.append(match)

    async def delete_manual_match(self, key):
        self.manual_matches = [
            _ for _ in self.manual_matches
            if _.key != key
        ]


class FakeSchedule(Schedule):
    date = START_DATE

    def now(self):
        return self.date


class FakeContext(Context):
    def __init__(self):
        Context.__init__(self)
        self.bot = FakeBot()
        self.dispatcher = Dispatcher(self.bot)
        self.broadcast = Broadcast(self.bot)
        self.db = FakeDB()
        self.schedule = FakeSchedule()


def fake_setup(context):
    setup_bot(context)

    Bot.set_current(context.bot)
    Dispatcher.set_current(context.dispatcher)


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
