
from datetime import timedelta as Timedelta

from neludim.obj import (
    User,
    Contact,
    ManualMatch,
)
from neludim.const import (
    MONTH_PERIOD,

    MAIN_ROUND,
    EXTRA_ROUND,

    CONFIRM_STATE,
    FAIL_STATE,
)

from neludim.tests.fake import (
    process_update,
    match_trace,
)


######
#  START
######


START_JSON = '{"message": {"message_id": 2, "from": {"id": 113947584, "is_bot": false, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "language_code": "ru"}, "chat": {"id": 113947584, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "type": "private"}, "date": 1659800990, "text": "/start", "entities": [{"type": "bot_command", "offset": 0, "length": 6}]}}'


async def test_start(context):
    await process_update(context, START_JSON)
    assert match_trace(context.bot.trace, [
        ['setMyCommands', '{"commands"'],
        ['sendMessage', 'С чего начать']
    ])

    user = context.db.users[0]
    assert user.username == 'alexkuk'
    assert user.created
    assert user.name == 'Alexander Kukushkin'


#######
#  PROFILE
######


async def test_edit_name(context):
    context.db.users = [User(user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/edit_profile'))
    await process_update(context, START_JSON.replace('/start', '/edit_name'))
    await process_update(context, START_JSON.replace('/start', 'Alexander Kukushkin'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Имя:'],
        ['sendMessage', '{"chat_id": 113947584, "text": "Напиши своё настоящее имя'],
        ['sendMessage', '{"chat_id": 113947584, "text": "Имя: Alexander Kukushkin'],
    ])
    assert context.db.users[0].name == 'Alexander Kukushkin'


async def test_edit_city(context):
    context.db.users = [User(user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/edit_city'))
    await process_update(context, START_JSON.replace('/start', 'Moscow'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Напиши город'],
        ['sendMessage', 'Город: Moscow'],
    ])
    assert context.db.users[0].city == 'Moscow'


async def test_edit_links(context):
    context.db.users = [User(user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/edit_links'))
    await process_update(context, START_JSON.replace('/start', 'vk.com/alexkuk'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Накидай ссылок'],
        ['sendMessage', 'Ссылки: vk.com/alexkuk'],
    ])
    assert context.db.users[0].links == 'vk.com/alexkuk'


async def test_edit_about(context):
    context.db.users = [User(user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/edit_about'))
    await process_update(context, START_JSON.replace('/start', 'Закончил ШАД, работал в Яндексе'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Напиши о себе'],
        ['sendMessage', 'Закончил ШАД, работал в Яндексе'],
    ])
    assert context.db.users[0].about == 'Закончил ШАД, работал в Яндексе'


async def test_empty_edit(context):
    context.db.users = [User(user_id=113947584, name='A K')]
    await process_update(context, START_JSON.replace('/start', '/edit_name'))
    await process_update(context, START_JSON.replace('/start', '/empty'))
    assert context.db.users[0].name is None


async def test_cancel_edit(context):
    context.db.users = [User(user_id=113947584, name='A K', links='vk.com/alexkuk')]
    await process_update(context, START_JSON.replace('/start', '/edit_links'))
    await process_update(context, START_JSON.replace('/start', '/cancel'))

    assert context.db.users == [User(user_id=113947584, name='A K', links='vk.com/alexkuk')]


#######
#   PARTICIPATE/PAUSE
#######


async def test_participate(context):
    context.db.users = [User(user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/participate'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Пометил, что участвуешь'],
    ])

    user = context.db.users[0]
    assert user.agreed_participate == context.schedule.now()
    assert user.paused is None


async def test_pause(context):
    context.db.users = [User(user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/pause_month'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Поставил встречи на паузу'],
    ])

    user = context.db.users[0]
    assert user.agreed_participate is None
    assert user.paused == context.schedule.now()
    assert user.pause_period == MONTH_PERIOD


#######
#  CONTACT
######


async def test_show_no_contact(context):
    context.db.users = [User(user_id=113947584, partner_user_id=None)]
    await process_update(context, START_JSON.replace('/start', '/show_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Бот не назначил'],
    ])


async def test_show_contact(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584)]
    context.db.contacts = [Contact(week_index=0, user_id=113947584, partner_user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/show_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Контакт собеседника'],
    ])


async def test_confirm_contact(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584)]
    context.db.contacts = [Contact(week_index=0, user_id=113947584, partner_user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/confirm_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'договорились'],
    ])
    assert context.db.contacts[0].state == CONFIRM_STATE


async def test_fail_main_contact(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584)]
    context.db.contacts = [Contact(week_index=0, user_id=113947584, partner_user_id=113947584, round=MAIN_ROUND)]
    await process_update(context, START_JSON.replace('/start', '/fail_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Бот подберет нового собеседника в четверг'],
    ])
    assert context.db.contacts[0].state == FAIL_STATE


async def test_fail_extra_contact(context):
    context.schedule.date += Timedelta(days=4)
    context.db.users = [User(user_id=113947584, partner_user_id=113947584)]
    context.db.contacts = [Contact(week_index=0, user_id=113947584, partner_user_id=113947584, round=EXTRA_ROUND)]
    await process_update(context, START_JSON.replace('/start', '/fail_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Пометил, что встреча не состоялась'],
    ])
    assert context.db.contacts[0].state == FAIL_STATE


async def test_contact_feedback(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584)]
    context.db.contacts = [Contact(week_index=0, user_id=113947584, partner_user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/contact_feedback'))
    await process_update(context, START_JSON.replace('/start', '3'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'очень плохо'],
        ['sendMessage', 'Фидбек'],
    ])
    assert context.db.contacts[0].feedback == '3'


######
#  TAG
#######


QUERY_JSON = '{"callback_query": {"id": "489401150900673103", "from": {"id": 113947584, "is_bot": false, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "language_code": "ru"}, "message": {"message_id": 3736, "from": {"id": 5580420387, "is_bot": true, "first_name": "Neludim", "username": "neludim_bot"}, "chat": {"id": 113947584, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "type": "private"}, "date": 1664010458, "text": "@adrien_и: ∅", "entities": [], "reply_markup": {}}, "chat_instance": "4489080918223338352", "data": "<data>"}}'


async def test_add_tag(context):
    context.db.users = [User(user_id=364501282)]
    await process_update(context, QUERY_JSON.replace('<data>', 'add_tag:364501282:krutan'))

    assert context.db.users[0].tags == ['krutan']


async def test_reset_tags(context):
    context.db.users = [User(user_id=364501282)]
    await process_update(context, QUERY_JSON.replace('<data>', 'delete_tags:364501282'))

    assert context.db.users[0].tags == []


async def test_confirm_tags(context):
    context.db.users = [User(user_id=364501282)]
    await process_update(context, QUERY_JSON.replace('<data>', 'confirm_tags:364501282'))

    assert context.db.users[0].confirmed_tags


######
#  MANUAL MATCH
#####


async def test_manual_match_bad_command(context):
    await process_update(context, START_JSON.replace('/start', '/manual_match alex'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Не смог'],
    ])
    

async def test_manual_match_empty_select(context):
    context.db.users = [User(user_id=364501282, username='kolya')]
    await process_update(context, START_JSON.replace('/start', '/manual_match alex ilya reason'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Не нашёл участника'],
    ])


async def test_manual_match_ambig_select(context):
    context.db.users = [
        User(user_id=364501282, username='alex'),
        User(user_id=364501283, name='alex')
    ]
    await process_update(context, START_JSON.replace('/start', '/manual_match alex bob reason'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Нашёл несколько участников'],
    ])


async def test_manual_match_ok(context):
    context.db.users = [
        User(user_id=364501282, username='Alex'),
        User(user_id=364501283, name='Bob')
    ]
    await process_update(context, START_JSON.replace('/start', '/manual_match alex bob reason'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Добавил метч'],
    ])
    assert context.db.manual_matches == [
        ManualMatch(user_id=364501282, partner_user_id=364501283, reason='reason')
    ]


#######
#   HELP/OTHER
#######


async def test_help(context):
    await process_update(context, START_JSON.replace('/start', '/help'))
    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Как это']
    ])


async def test_other(context):
    await process_update(context, START_JSON.replace('/start', 'abc'))
    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Как это']
    ])
