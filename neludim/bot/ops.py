
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from neludim.const import (
    ADMIN_USER_ID,

    CONFIRM_STATE,
    FAIL_STATE,

    GREAT_SCORE,
    OK_SCORE,
    BAD_SCORE,
)
from neludim.text import (
    day_month,
    user_mention,
    profile_text,
)

from neludim.schedule import week_index
from neludim.obj import (
    Match,
    Contact,
)
from neludim.match import gen_matches
from neludim.report import (
    gen_match_report,
    format_match_report,
    gen_weeks_report,
    format_weeks_report,
    report_text
)

from .data import (
    serialize_data,
    ParticipateData,
    FeedbackData
)


#######
#
#   ASK PARTICIPATE
#
####


def ask_participate_text(context):
    return f'''Участвуешь во встречах на следующей неделе? Если дашь согласие, в понедельник {day_month(context.schedule.next_week_monday())} бот пришлёт анкету и контакт собеседника.

Бот просит подтверждать участие каждую неделю. Подбирает собеседника из тех, кто согласился.'''


def ask_participate_markup(context):
    week_index = context.schedule.current_week_index() + 1
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(
            text='✓ Участвую',
            callback_data=serialize_data(ParticipateData(week_index, agreed=1))
        ),
        InlineKeyboardButton(
            text='✗ Пропускаю неделю',
            callback_data=serialize_data(ParticipateData(week_index, agreed=0))
        ),
    )


async def ask_participate(context):
    users = await context.db.read_users()

    for user in users:
        await context.broadcast.send_message(
            chat_id=user.user_id,
            text=ask_participate_text(context),
            reply_markup=ask_participate_markup(context)
        )


######
#
#   CREATE CONTACTS
#
####


async def create_contacts(context):
    users = await context.db.read_users()
    contacts = await context.db.read_contacts()
    manual_matches = await context.db.read_manual_matches()
    current_week_index = context.schedule.current_week_index()

    participate_users = [
        _ for _ in users
        if (
                _.agreed_participate
                and week_index(_.agreed_participate) == current_week_index - 1
        )
    ]
    skip_matches = [
        Match(_.user_id, _.partner_user_id)
        for _ in contacts
    ]
    matches = list(gen_matches(participate_users, skip_matches, manual_matches))

    contacts = []
    for match in matches:
        user_id, partner_user_id = match.key

        contacts.append(Contact(
            week_index=current_week_index,
            user_id=user_id,
            partner_user_id=partner_user_id
        ))

        if partner_user_id:
            contacts.append(Contact(
                week_index=current_week_index,
                user_id=partner_user_id,
                partner_user_id=user_id
            ))

    for user in users:
        user.partner_user_id = None

    id_users = {_.user_id: _ for _ in users}
    for match in matches:
        user_id, partner_user_id = match.key

        user = id_users[user_id]
        user.partner_user_id = partner_user_id

        if partner_user_id:
            partner_user = id_users[partner_user_id]
            partner_user.partner_user_id = user_id

    await context.db.put_contacts(contacts)
    await context.db.put_users(users)


######
#
#   SEND CONTACTS
#
####


def send_contact_text(user):
    return f'''Бот подобрал тебе собеседника! Его контакт в Телеграме: {user_mention(user)}. Пожалуйста, договоритесь про время и место встречи.

{profile_text(user)}'''


def no_contact_text(context):
    return f'''Бот не смог подобрать тебе собеседника. Такое бывает, когда число участников нечетное. Бот исключает одного случайного.

Бот пришлёт новое приглашение в конце недели. Если согласишься участвовать, бот повторит попытку в понедельник {day_month(context.schedule.next_week_monday())}.'''


async def send_contacts(context):
    id_users = {
        _.user_id: _
        for _ in await context.db.read_users()
    }
    week_contacts = [
        _ for _ in await context.db.read_contacts()
        if _.week_index == context.schedule.current_week_index()
    ]

    for contact in week_contacts:
        if contact.partner_user_id:
            partner_user = id_users[contact.partner_user_id]
            await context.broadcast.send_message(
                chat_id=contact.user_id,
                text=send_contact_text(partner_user),
            )
        else:
            await context.broadcast.send_message(
                chat_id=contact.user_id,
                text=no_contact_text(context)
            )


######
#
#  ASK FEEDBACK
#
#####


def ask_feedback_text(partner_user):
    return f'''Как прошла встреча с {user_mention(partner_user)}?

Бот использует фидбек, чтобы лучше подбирать собеседников.'''


def ask_feedback_markup(context, partner_user):
    current_week_index = context.schedule.current_week_index()
    partner_user_id = partner_user.user_id
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(
            text='👍 Хорошо',
            callback_data=serialize_data(FeedbackData(
                current_week_index, partner_user_id,
                state=CONFIRM_STATE,
                feedback_score=GREAT_SCORE
            ))
        ),
        InlineKeyboardButton(
            text='👌 Средне',
            callback_data=serialize_data(FeedbackData(
                current_week_index, partner_user_id,
                state=CONFIRM_STATE,
                feedback_score=OK_SCORE
            ))
        ),
        InlineKeyboardButton(
            text='👎 Плохо',
            callback_data=serialize_data(FeedbackData(
                current_week_index, partner_user_id,
                state=CONFIRM_STATE,
                feedback_score=BAD_SCORE
            ))
        ),
        InlineKeyboardButton(
            text='✗ Встреча не состоялась',
            callback_data=serialize_data(FeedbackData(
                current_week_index, partner_user_id,
                state=FAIL_STATE,
            ))
        )
    )


async def ask_feedback(context):
    id_users = {
        _.user_id: _
        for _ in await context.db.read_users()
    }
    week_contacts = [
        _ for _ in await context.db.read_contacts()
        if _.week_index == context.schedule.current_week_index()
    ]

    for contact in week_contacts:
        if not contact.partner_user_id:
            continue

        partner_user = id_users[contact.partner_user_id]
        await context.broadcast.send_message(
            chat_id=contact.user_id,
            text=ask_feedback_text(partner_user),
            reply_markup=ask_feedback_markup(context, partner_user)
        )


######
#
#   SEND MANUAL MATCHES
#
#####


def manual_match_text(user, partner_user):
    return f'manual_match {user_mention(user)} -> {user_mention(partner_user)}'


async def send_manual_matches(context):
    contacts = await context.db.read_contacts()
    manual_matches = await context.db.read_manual_matches()
    id_users = {
        _.user_id: _
        for _ in await context.db.read_users()
    }

    skip_matches = set()
    for contact in contacts:
        if contact.partner_user_id:
            skip_matches.add((contact.user_id, contact.partner_user_id))
            skip_matches.add((contact.partner_user_id, contact.user_id))

    for match in manual_matches:
        if (
                (match.user_id, match.partner_user_id) not in skip_matches
                and (match.partner_user_id, match.user_id) not in skip_matches
                and ADMIN_USER_ID in (match.user_id, match.partner_user_id)
        ):
            user = id_users[match.user_id]
            partner_user = id_users[match.partner_user_id]
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=manual_match_text(user, partner_user)
            )


######
#
#   SEND REPORTS
#
######


async def send_reports(context):
    id_users = {
        _.user_id: _
        for _ in await context.db.read_users()
    }
    contacts = await context.db.read_contacts()
    current_week_index = context.schedule.current_week_index()

    records = gen_weeks_report(contacts)
    lines = format_weeks_report(records)
    text = report_text(lines, html=True)
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=text
    )

    week_contacts = [
        _ for _ in contacts
        if _.week_index == current_week_index - 1
    ]
    records = gen_match_report(week_contacts)
    lines = format_match_report(records, id_users)
    text = report_text(lines, html=True)
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=text
    )

    week_contacts = [
        _ for _ in contacts
        if _.week_index == current_week_index
    ]
    records = gen_match_report(week_contacts)
    lines = format_match_report(records, id_users)
    text = report_text(lines, html=True)
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=text
    )
