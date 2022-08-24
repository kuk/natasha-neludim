
from neludim.tests.fake import (
    context,
    match_trace
)

from neludim.const import (
    CONFIRM_STATE,
    FAIL_STATE,
)
from neludim.obj import (
    User,
    Contact,
)
from neludim.ops import (
    confirm_contact_op,
    contact_feedback_op,
)


USERS = [
    User(user_id=1, username='a'),
    User(user_id=2, username='b'),
    User(user_id=3, username='c'),
    User(user_id=4, username='d'),
]


async def test_broadcast_confirm_contact(context):
    context.db.users = USERS
    context.db.contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2),
        Contact(week_index=0, user_id=2, partner_user_id=1),
        Contact(week_index=0, user_id=3, partner_user_id=4, state=CONFIRM_STATE),
        Contact(week_index=0, user_id=4, partner_user_id=3),
    ]
    
    await confirm_contact_op(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '@b'],
        ['sendMessage', '@a'],
    ])


async def test_broadcast_contact_feedback(context):
    context.db.users = USERS
    context.db.contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2, state=FAIL_STATE),
        Contact(week_index=0, user_id=2, partner_user_id=1, feedback='1'),
        Contact(week_index=0, user_id=3, partner_user_id=4, state=CONFIRM_STATE),
    ]
    
    await contact_feedback_op(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '@d'],
    ])
