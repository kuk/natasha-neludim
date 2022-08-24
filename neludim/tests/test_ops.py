
from neludim.tests.fake import (
    context,
    match_trace
)

from neludim.const import (
    CONFIRM_STATE,
    FAIL_STATE,

    WEEK,
    MONTH,
)
from neludim.obj import (
    User,
    Contact,
)
from neludim.schedule import week_index_monday
    
from neludim.ops import (
    ask_agree_participate,
    ask_confirm_contact,
    ask_contact_feedback,
)


async def test_ask_agree_participate(context):
    week_index = context.schedule.current_week_index()
    context.db.users = [
        User(user_id=0),
        User(user_id=1, agreed_participate=week_index_monday(week_index - 1)),
        User(user_id=2, agreed_participate=week_index_monday(week_index)),
        User(user_id=3, paused=week_index_monday(week_index - 1), pause_period=WEEK),
        User(user_id=4, paused=week_index_monday(week_index), pause_period=WEEK),
        User(user_id=5, paused=week_index_monday(week_index - 3), pause_period=MONTH),
        User(user_id=6, paused=week_index_monday(week_index - 4), pause_period=MONTH),
    ]
    await ask_agree_participate(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '"chat_id": 0'],
        ['sendMessage', '"chat_id": 1'],
        ['sendMessage', '"chat_id": 3'],
        ['sendMessage', '"chat_id": 6'],
    ])


async def test_ask_confirm_contact(context):
    context.db.users = [
        User(user_id=1, username='a'),
        User(user_id=2, username='b'),
        User(user_id=3),
        User(user_id=4),
    ]
    context.db.contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2),
        Contact(week_index=0, user_id=2, partner_user_id=1),
        Contact(week_index=0, user_id=3, partner_user_id=4, state=CONFIRM_STATE),
        Contact(week_index=0, user_id=4, partner_user_id=3),
    ]
    
    await ask_confirm_contact(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '@b'],
        ['sendMessage', '@a'],
    ])


async def test_ask_contact_feedback(context):
    context.db.users = [
        User(user_id=1),
        User(user_id=2),
        User(user_id=3),
        User(user_id=4, username='d'),
    ]
    context.db.contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2, state=FAIL_STATE),
        Contact(week_index=0, user_id=2, partner_user_id=1, feedback='1'),
        Contact(week_index=0, user_id=3, partner_user_id=4, state=CONFIRM_STATE),
    ]
    
    await ask_contact_feedback(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '@d'],
    ])
