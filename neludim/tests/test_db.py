
from neludim.obj import (
    User,
    Intro,
    Contact,
    Match
)


async def test_chats(db):
    await db.set_chat_state(1, '2')
    assert '2' == await db.get_chat_state(1)


async def test_users(db):
    user = User(
        user_id=1,
        intro=Intro(
            name='abc'
        )
    )

    await db.put_user(user)
    assert user == await db.get_user(user_id=user.user_id)
    assert user in await db.read_users()

    await db.delete_user(user_id=user.user_id)
    assert await db.get_user(user_id=user.user_id) is None
    

async def test_contacts(db):
    contact = Contact(
        week_index=0,
        user_id=1,
        partner_user_id=2
    )

    await db.put_contact(contact)
    assert contact == await db.get_contact(contact.key)
    assert contact in await db.read_contacts()

    await db.delete_contact(contact.key)
    assert await db.get_contact(contact.key) is None


async def test_manual_matches(db):
    match = Match(
        user_id=1,
        partner_user_id=2,
    )

    await db.put_manual_match(match)
    assert match in await db.read_manual_matches()
    await db.delete_manual_match(match.key)
