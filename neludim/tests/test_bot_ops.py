
from neludim.tests.fake import match_trace

from neludim.obj import (
    User,
    Contact,
)
from neludim.schedule import week_index_monday

from neludim.bot.ops import (
    ask_participate,
    create_contacts,
    send_contacts,
    ask_feedback,
    manual_match,
    send_reports
)


async def test_ask_participate(context):
    context.db.users = [
        User(user_id=0)
    ]
    await ask_participate(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '"chat_id": 0'],
    ])


async def test_create_contacts(context):
    agreed_participate = week_index_monday(context.schedule.current_week_index() - 1)
    context.db.users = [
        User(user_id=1, agreed_participate=agreed_participate),
        User(user_id=2, agreed_participate=agreed_participate),
        User(user_id=3, agreed_participate=agreed_participate),
    ]
    await create_contacts(context)
    assert context.db.contacts == [
        Contact(week_index=0, user_id=2, partner_user_id=3),
        Contact(week_index=0, user_id=3, partner_user_id=2),
        Contact(week_index=0, user_id=1, partner_user_id=None),
    ]


async def test_send_contacts(context):
    context.db.users = [
        User(user_id=1),
        User(user_id=2),
        User(user_id=3),
    ]
    context.db.contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=3),
        Contact(week_index=0, user_id=3, partner_user_id=1),
        Contact(week_index=0, user_id=2, partner_user_id=None),
    ]
    await send_contacts(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 1, "text": "Бот подобрал'],
        ['sendMessage', '{"chat_id": 3, "text": "Бот подобрал'],
        ['sendMessage', '{"chat_id": 2, "text": "Бот не смог подобрать'],
    ])


async def test_ask_feedback(context):
    context.db.users = [
        User(user_id=1, username='a'),
        User(user_id=2, username='b'),
        User(user_id=3),
    ]
    context.db.contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2),
        Contact(week_index=0, user_id=2, partner_user_id=1),
        Contact(week_index=0, user_id=3, partner_user_id=None),
    ]
    await ask_feedback(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '@b'],
        ['sendMessage', '@a'],
    ])


async def test_manual_match(context):
    agreed_participate = week_index_monday(context.schedule.current_week_index())
    context.db.users = [
        User(user_id=1, username='a', created=0, agreed_participate=agreed_participate),
        User(user_id=2, username='b', created=0, agreed_participate=agreed_participate),
    ]
    await manual_match(context)
    assert match_trace(context.bot.trace, [
        ['sendMessage', '1 @a'],
        ['sendMessage', 'user: ∅'],
    ])


async def test_send_reports(context):
    await send_reports(context)
