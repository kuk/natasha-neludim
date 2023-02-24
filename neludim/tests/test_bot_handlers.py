
from neludim.obj import (
    User,
    Contact,
)

from neludim.tests.fake import (
    process_update,
    match_trace,
)


def message_json(text):
    return '{"message": {"message_id": 2, "from": {"id": 1, "is_bot": false, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "language_code": "ru"}, "chat": {"id": 1, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "type": "private"}, "date": 1659800990, "text": "%s", "entities": []}}' % text


def query_json(data):
    return '{"callback_query": {"id": "1", "from": {"id": 1, "is_bot": false, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "language_code": "ru"}, "message": {"message_id": 1, "from": {"id": 2, "is_bot": true, "first_name": "Neludim", "username": "neludim_bot"}, "chat": {"id": 1, "first_name": "Alexander", "last_name": "Kukushkin", "username": "alexkuk", "type": "private"}, "date": 1664010458, "text": "", "entities": [], "reply_markup": {}}, "chat_instance": "1", "data": "%s"}}' % data


######
#
#  START
#
######


async def test_start(context):
    await process_update(context, message_json('/start'))
    assert match_trace(context.bot.trace, [
        ['setMyCommands', '{"commands"'],
        ['sendMessage', 'Бот Нелюдим']
    ])

    user = context.db.users[0]
    assert user.username == 'alexkuk'
    assert user.created
    assert user.name == 'Alexander Kukushkin'


#######
#
#  PROFILE
#
######


async def test_edit_profile(context):
    context.db.users = [User(user_id=1)]
    await process_update(context, query_json('edit_profile:'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', '{"chat_id": 1, "text": "Имя:'],
    ])


async def test_edit_name(context):
    context.db.users = [User(user_id=1)]
    await process_update(context, query_json('edit_profile:name'))
    await process_update(context, message_json('Alexander Kukushkin'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', '{"chat_id": 1, "text": "Напиши своё настоящее имя'],
        ['sendMessage', '{"chat_id": 1, "text": "Имя: Alexander Kukushkin'],
    ])
    assert context.db.users[0].name == 'Alexander Kukushkin'


async def test_edit_city(context):
    context.db.users = [User(user_id=1)]
    await process_update(context, query_json('edit_profile:city'))
    await process_update(context, message_json('Moscow'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', '{"chat_id": 1, "text": "Напиши город'],
        ['sendMessage', 'Город: Moscow'],
    ])
    assert context.db.users[0].city == 'Moscow'


async def test_edit_links(context):
    context.db.users = [User(user_id=1)]
    await process_update(context, query_json('edit_profile:links'))
    await process_update(context, message_json('vk.com/alexkuk'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', '{"chat_id": 1, "text": "Накидай ссылок'],
        ['sendMessage', 'Ссылки: vk.com/alexkuk'],
    ])
    assert context.db.users[0].links == 'vk.com/alexkuk'


async def test_edit_about(context):
    context.db.users = [User(user_id=1)]
    await process_update(context, query_json('edit_profile:about'))
    await process_update(context, message_json('Закончил ШАД, работал в Яндексе'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', '{"chat_id": 1, "text": "Напиши о себе'],
        ['sendMessage', 'Закончил ШАД, работал в Яндексе'],
    ])
    assert context.db.users[0].about == 'Закончил ШАД, работал в Яндексе'


async def test_cancel_edit(context):
    await process_update(context, query_json('cancel_edit'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['deleteMessage', '{"chat_id": 1, "message_id": 1}']
    ])


#######
#
#   PARTICIPATE
#
#######


async def test_participate(context):
    context.db.users = [User(user_id=1)]
    await process_update(context, query_json('participate:1:1'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendSticker', '{"chat_id": 1'],
        ['sendMessage', 'Пометил, что участвуешь'],
    ])

    user = context.db.users[0]
    assert user.agreed_participate == context.schedule.now()


async def test_no_participate(context):
    context.db.users = [User(user_id=1)]
    await process_update(context, query_json('participate:1:0'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', 'Пометил, что не участвуешь'],
    ])

    user = context.db.users[0]
    assert not user.agreed_participate


async def test_late_participate(context):
    context.db.users = [User(user_id=1)]
    await process_update(context, query_json('participate:0:1'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', 'Не дождался твоего ответа'],
    ])

    user = context.db.users[0]
    assert not user.agreed_participate


######
#
#   FEEDBACK
#
######


async def test_feedback(context):
    context.db.users = [User(user_id=1, partner_user_id=2)]
    context.db.contacts = [Contact(week_index=0, user_id=1, partner_user_id=2)]
    await process_update(context, query_json('feedback:0:2:confirm:great'))
    await process_update(context, message_json('Все круто'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', 'Дай, пожалуйста, фидбек'],
        ['sendMessage', 'Спасибо'],
    ])
    assert context.db.contacts[0].feedback_text == 'Все круто'


async def test_bad_feedback(context):
    context.db.users = [User(user_id=1, partner_user_id=2)]
    context.db.contacts = [Contact(week_index=0, user_id=1, partner_user_id=2)]
    await process_update(context, query_json('feedback:0:2:confirm:bad'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', 'Напиши, пожалуйста, что не понравилось'],
    ])


async def test_fail_feedback(context):
    context.db.users = [User(user_id=1, partner_user_id=2)]
    context.db.contacts = [Contact(week_index=0, user_id=1, partner_user_id=2)]
    await process_update(context, query_json('feedback:0:2:fail:'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', 'Напиши, пожалуйста, почему встреча не состоялась'],
    ])


async def test_cancel_feedback(context):
    await process_update(context, query_json('cancel_feedback'))

    assert match_trace(context.bot.trace, [
        ['answerCallbackQuery', '{"callback_query_id": "1"}'],
        ['sendMessage', 'спасибо'],
    ])


#######
#   HELP/OTHER
#######


async def test_help(context):
    await process_update(context, message_json('/help'))
    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Бот Нелюдим']
    ])


async def test_other(context):
    await process_update(context, message_json('abc'))
    assert match_trace(context.bot.trace, [
        ['sendMessage', 'Бот Нелюдим']
    ])


#####
#  V1
#######


async def test_v1_commands(context):
    await process_update(context, message_json('/show_contact'))
    assert match_trace(context.bot.trace, [
        ['sendMessage', 'обновил интерфейс бота']
    ])
