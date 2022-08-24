
from neludim.tests.fake import (
    context,
    match_trace
)

from neludim.const import (
    CONFIRM_STATE
)
from neludim.obj import (
    User,
    Contact
)
from neludim.ops import (
    broadcast_confirm_contact,
)


async def test_broadcast_confirm_contact(context):
    context.db.users = [
        User(user_id=1, username='1'),
        User(user_id=2, username='2')
    ]
    context.db.contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2),
        Contact(week_index=0, user_id=2, partner_user_id=1),
    ]
    
    await broadcast_confirm_contact(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Получилось договориться'],
        ['sendMessage', 'Получилось договориться'],
    ])


async def test_broadcast_confirm_contact_skip(context):
    context.db.users = [
        User(user_id=1, username='1'),
        User(user_id=2, username='2')
    ]
    context.db.contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2, state=CONFIRM_STATE),
        Contact(week_index=0, user_id=2, partner_user_id=1),
    ]
    
    await broadcast_confirm_contact(context)
    assert match_trace(context.bot.trace, [])
