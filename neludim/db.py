
from .obj import (
    Chat,
    Contact,
    User,
    Match,
)
from .const import (
    CHATS_TABLE,
    CHATS_KEY,

    USERS_TABLE,
    USERS_KEY,

    CONTACTS_TABLE,
    CONTACTS_KEY,

    MANUAL_MATCHES_TABLE,
    MANUAL_MATCHES_KEY,

    N, S,
)
from .dynamo import (
    dynamo_client,

    dynamo_get,
    dynamo_scan,
    dynamo_batch_delete,
    dynamo_batch_put,

    dynamo_deserialize_item,
    dynamo_serialize_item,
    dynamo_serialize_key,
)


#######
#
#   CHATS
#
#######


async def get_chat(db, id):
    item = await dynamo_get(
        db.client, CHATS_TABLE,
        CHATS_KEY, N, id
    )
    if item:
        return dynamo_deserialize_item(item, Chat)


async def put_chat(db, chat):
    item = dynamo_serialize_item(chat)
    await dynamo_batch_put(db.client, CHATS_TABLE, [item])


async def get_chat_state(db, id):
    chat = await get_chat(db, id)
    if chat:
        return chat.state


async def set_chat_state(db, id, state):
    chat = Chat(id, state)
    await put_chat(db, chat)


######
#
#   USERS
#
#######


async def get_user(db, user_id):
    item = await dynamo_get(
        db.client, USERS_TABLE,
        USERS_KEY, N, user_id
    )
    if item:
        return dynamo_deserialize_item(item, User)


async def read_users(db):
    items = await dynamo_scan(db.client, USERS_TABLE)
    return [dynamo_deserialize_item(_, User) for _ in items]


async def put_users(db, users):
    items = (dynamo_serialize_item(_) for _ in users)
    await dynamo_batch_put(db.client, USERS_TABLE, items)


async def delete_users(db, user_ids):
    await dynamo_batch_delete(
        db.client, USERS_TABLE,
        USERS_KEY, N, user_ids
    )


async def put_user(db, user):
    await put_users(db, [user])


async def delete_user(db, user_id):
    await delete_users(db, [user_id])


#######
#
#   CONTACTS
#
#####


async def get_contact(db, key):
    item = await dynamo_get(
        db.client, CONTACTS_TABLE,
        CONTACTS_KEY, S, dynamo_serialize_key(key)
    )
    if item:
        return dynamo_deserialize_item(item, Contact)


async def read_contacts(db):
    items = await dynamo_scan(db.client, CONTACTS_TABLE)
    return [dynamo_deserialize_item(_, Contact) for _ in items]


def serialize_contact(contact):
    item = dynamo_serialize_item(contact)
    item[CONTACTS_KEY] = {S: dynamo_serialize_key(contact.key)}
    return item


async def put_contacts(db, contacts):
    items = (serialize_contact(_) for _ in contacts)
    await dynamo_batch_put(db.client, CONTACTS_TABLE, items)


async def delete_contacts(db, keys):
    keys = (dynamo_serialize_key(_) for _ in keys)
    await dynamo_batch_delete(
        db.client, CONTACTS_TABLE,
        CONTACTS_KEY, S, keys
    )


async def put_contact(db, contact):
    await put_contacts(db, [contact])


async def delete_contact(db, key):
    await delete_contacts(db, [key])


#######
#
#    MANUAL MATCHES
#
######


async def read_manual_matches(db):
    items = await dynamo_scan(db.client, MANUAL_MATCHES_TABLE)
    return [dynamo_deserialize_item(_, Match) for _ in items]


def serialize_manual_match(match):
    item = dynamo_serialize_item(match)
    item[MANUAL_MATCHES_KEY] = {S: dynamo_serialize_key(match.key)}
    return item


async def put_manual_matches(db, matches):
    items = (serialize_manual_match(_) for _ in matches)
    await dynamo_batch_put(db.client, MANUAL_MATCHES_TABLE, items)


async def delete_manual_matches(db, keys):
    keys = (dynamo_serialize_key(_) for _ in keys)
    await dynamo_batch_delete(
        db.client, MANUAL_MATCHES_TABLE,
        MANUAL_MATCHES_KEY, S, keys
    )


async def put_manual_match(db, match):
    await put_manual_matches(db, [match])


async def delete_manual_match(db, key):
    await delete_manual_matches(db, [key])


######
#
#  DB
#
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

DB.get_user = get_user
DB.read_users = read_users
DB.put_user = put_user
DB.delete_user = delete_user
DB.put_users = put_users
DB.delete_users = delete_users

DB.get_contact = get_contact
DB.read_contacts = read_contacts
DB.put_contact = put_contact
DB.delete_contact = delete_contact
DB.put_contacts = put_contacts
DB.delete_contacts = delete_contacts

DB.read_manual_matches = read_manual_matches
DB.put_manual_match = put_manual_match
DB.delete_manual_match = delete_manual_match
DB.put_manual_matches = put_manual_matches
DB.delete_manual_matches = delete_manual_matches
