
from .obj import (
    Chat,
    Contact,
    User,
)
from .const import (
    CHATS_TABLE,
    CHATS_KEY,

    USERS_TABLE,
    USERS_KEY,

    CONTACTS_TABLE,
    CONTACTS_KEY,

    N, S,
)
from .dynamo import (
    dynamo_client,
    dynamo_put,
    dynamo_get,
    dynamo_delete,
    dynamo_scan,
    dynamo_deserialize_item,
    dynamo_serialize_item,
    dynamo_key,
)


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
