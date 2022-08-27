
from neludim.obj import (
    User,
    Intro,
    Contact,
)
from neludim.const import (
    MONTH,

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
        ['sendMessage', '{"chat_id": 113947584, "text": "Бот организует']
    ])
    assert context.db.users == [User(user_id=113947584, username='alexkuk', intro=Intro(name='Alexander Kukushkin'))]


#######
#  INTRO
######


async def test_edit_name(context):
    context.db.users = [User(user_id=113947584, intro=Intro())]
    await process_update(context, START_JSON.replace('/start', '/edit_intro'))
    await process_update(context, START_JSON.replace('/start', '/edit_name'))
    await process_update(context, START_JSON.replace('/start', 'Alexander Kukushkin'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Имя:'],
        ['sendMessage', '{"chat_id": 113947584, "text": "Напиши своё настоящее имя'],
        ['sendMessage', '{"chat_id": 113947584, "text": "Имя: Alexander Kukushkin'],
    ])
    assert context.db.users[0].intro.name == 'Alexander Kukushkin'


async def test_edit_city(context):
    context.db.users = [User(user_id=113947584, intro=Intro())]
    await process_update(context, START_JSON.replace('/start', '/edit_city'))
    await process_update(context, START_JSON.replace('/start', 'Moscow'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Напиши город'],
        ['sendMessage', 'Город: Moscow'],
    ])
    assert context.db.users[0].intro.city == 'Moscow'


async def test_edit_links(context):
    context.db.users = [User(user_id=113947584, intro=Intro())]
    await process_update(context, START_JSON.replace('/start', '/edit_links'))
    await process_update(context, START_JSON.replace('/start', 'vk.com/alexkuk'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Накидай ссылок'],
        ['sendMessage', 'Ссылки: vk.com/alexkuk'],
    ])
    assert context.db.users[0].intro.links == 'vk.com/alexkuk'


async def test_edit_about(context):
    context.db.users = [User(user_id=113947584, intro=Intro())]
    await process_update(context, START_JSON.replace('/start', '/edit_about'))
    await process_update(context, START_JSON.replace('/start', 'Закончил ШАД, работал в Яндексе'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', '{"chat_id": 113947584, "text": "Напиши о себе'],
        ['sendMessage', 'Закончил ШАД, работал в Яндексе'],
    ])
    assert context.db.users[0].intro.about == 'Закончил ШАД, работал в Яндексе'


async def test_empty_edit(context):
    context.db.users = [User(user_id=113947584, intro=Intro(name='A K'))]
    await process_update(context, START_JSON.replace('/start', '/edit_name'))
    await process_update(context, START_JSON.replace('/start', '/empty'))
    assert context.db.users[0].intro.name is None


async def test_cancel_edit(context):
    context.db.users = [User(user_id=113947584, intro=Intro(name='A K', links='vk.com/alexkuk'))]
    await process_update(context, START_JSON.replace('/start', '/edit_links'))
    await process_update(context, START_JSON.replace('/start', '/cancel'))

    assert context.db.users == [User(user_id=113947584, intro=Intro(name='A K', links='vk.com/alexkuk'))]


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
    assert user.pause_period == MONTH


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
    context.db.users = [User(user_id=113947584, partner_user_id=113947584, intro=Intro())]
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


async def test_fail_contact(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584)]
    context.db.contacts = [Contact(week_index=0, user_id=113947584, partner_user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/fail_contact'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Жалко'],
    ])
    assert context.db.contacts[0].state == FAIL_STATE


async def test_contact_feedback(context):
    context.db.users = [User(user_id=113947584, partner_user_id=113947584, intro=Intro())]
    context.db.contacts = [Contact(week_index=0, user_id=113947584, partner_user_id=113947584)]
    await process_update(context, START_JSON.replace('/start', '/contact_feedback'))
    await process_update(context, START_JSON.replace('/start', '3'))

    assert match_trace(context.bot.trace, [
        ['sendMessage', 'очень плохо'],
        ['sendMessage', 'Записал фидбек'],
    ])
    assert context.db.contacts[0].feedback == '3'


#######
#   OTHER/STUB
#######


async def test_other(context):
    await process_update(context, START_JSON.replace('/start', 'abc'))
    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Бот организует']
    ])
