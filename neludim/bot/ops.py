
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

    SELECT_USER_ACTION,
)
from neludim.text import (
    EMPTY_SYMBOL,
    day_month,
    user_mention,
    profile_text,
)

from neludim.schedule import week_index
from neludim.obj import Contact

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
    FeedbackData,
    ManualMatchData,
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
    matches = list(gen_matches(
        participate_users,
        manual_matches=manual_matches,
        contacts=contacts,
        current_week_index=current_week_index,
    ))

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


#######
#
#   MANUAL MATCH
#
#####


def cap_text(text, max_size=10):
    lines = text.splitlines()
    if len(lines) > max_size:
        lines = lines[:max_size] + ['...']
    return '\n'.join(lines)


def manual_match_profile_texts(users):
    text = ''
    for index, user in enumerate(users, 1):
        sep = '\n\n' if text else ''
        chunk = f'''{sep}{index} {user_mention(user)}
{cap_text(profile_text(user))}'''

        # https://core.telegram.org/bots/api#sendmessage "Text of the
        # message to be sent, 1-4096 characters after entities
        # parsing". Assume len(text) == "length after parsing"
        if len(text) + len(chunk) > 4096:
            yield text
            text = ''
        text += chunk

    if text:
        yield text


MANUAL_MATCH_TEXT = f'''user: {EMPTY_SYMBOL}
partner user: {EMPTY_SYMBOL}'''


def manual_match_markup(users):
    # Max width = 8. Max buttons = 100, won't manually match more any
    # way
    markup = InlineKeyboardMarkup(row_width=5)
    for index, user in enumerate(users[:100], 1):
        button = InlineKeyboardButton(
            text=str(index),
            callback_data=serialize_data(ManualMatchData(
                action=SELECT_USER_ACTION,
                user_id=user.user_id
            ))
        )
        markup.insert(button)
    return markup


async def manual_match(context):
    users = await context.db.read_users()
    current_week_index = context.schedule.current_week_index()

    users = [
        _ for _ in users
        if (
                _.user_id == ADMIN_USER_ID
                or (
                    _.agreed_participate
                    and week_index(_.agreed_participate) == current_week_index
                )
        )
    ]
    users = sorted(users, key=lambda _: _.created)

    for text in manual_match_profile_texts(users):
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=text
        )

    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=MANUAL_MATCH_TEXT,
        reply_markup=manual_match_markup(users)
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
    manual_matches = await context.db.read_manual_matches()
    current_week_index = context.schedule.current_week_index()

    records = gen_weeks_report(contacts)
    lines = format_weeks_report(records)
    text = report_text(lines, html=True)
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=text
    )

    prev_contacts = [_ for _ in contacts if _.week_index < current_week_index - 1]
    week_contacts = [_ for _ in contacts if _.week_index == current_week_index - 1]
    records = gen_match_report(week_contacts, prev_contacts, manual_matches)
    lines = format_match_report(records, id_users)
    text = report_text(lines, html=True)
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=text
    )

    prev_contacts = [_ for _ in contacts if _.week_index < current_week_index]
    week_contacts = [_ for _ in contacts if _.week_index == current_week_index]
    records = gen_match_report(week_contacts, prev_contacts, manual_matches)
    lines = format_match_report(records, id_users)
    text = report_text(lines, html=True)
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=text
    )
