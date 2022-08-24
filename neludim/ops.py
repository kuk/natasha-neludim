
from .const import (
    CONFIRM_CONTACT_COMMAND,
    FAIL_CONTACT_COMMAND,
    CONTACT_FEEDBACK_COMMAND,

    CONFIRM_STATE,
    FAIL_STATE
)
from .text import (
    user_url,
    user_mention
)

from .bot.broadcast import (
    BroadcastTask,
    broadcast
)


#######
#
#  TEXT
#
####


def confirm_contact_text(user):
    return f'''Получилось договориться с <a href="{user_url(user.user_id)}">{user_mention(user)}</a> о встрече?

/{CONFIRM_CONTACT_COMMAND} - да, договорились
/{FAIL_CONTACT_COMMAND} - нет, не договорились/не отвечает'''


def contact_feedback_text(user):
    return f'''Оставь, пожалуйста, фидбек о встрече с <a href="{user_url(user.user_id)}">{user_mention(user)}</a>.

/{CONTACT_FEEDBACK_COMMAND} - оставить фидбек
/{FAIL_CONTACT_COMMAND} - встреча не состоялась

Бот просит оценить встречу от 1 до 5, использует фидбек, чтобы лучше подбирать собеседников.'''


######
#
#   OPS
#
######


def find_contacts(contacts, week_index=None):
    for contact in contacts:
        if week_index is not None and contact.week_index == week_index:
            yield contact


def find_user(users, user_id=None, username=None):
    for user in users:
        if (
                user_id is not None and user.user_id == user_id
                or username is not None and user.username == username
        ):
            return user


async def confirm_contact_op(context):
    users = await context.db.read_users()

    contacts = await context.db.read_contacts()
    week_id = context.schedule.current_week_index()
    contacts = find_contacts(contacts, week_index=week_id)

    tasks = []
    skip_user_ids = set()
    for contact in contacts:
        if (
                contact.state in (CONFIRM_STATE, FAIL_STATE)
                or contact.feedback
        ):
            skip_user_ids.add(contact.user_id)
            skip_user_ids.add(contact.partner_user_id)
            continue

        # If skip a->b, also skip b->a
        if contact.user_id in skip_user_ids:
            continue

        partner_user = find_user(users, user_id=contact.partner_user_id)
        text = confirm_contact_text(partner_user)
        tasks.append(BroadcastTask(
            chat_id=contact.user_id,
            text=text
        ))

    await broadcast(context.bot, tasks)


async def contact_feedback_op(context):
    users = await context.db.read_users()

    contacts = await context.db.read_contacts()
    week_id = context.schedule.current_week_index()
    contacts = find_contacts(contacts, week_index=week_id)

    tasks = []
    for contact in contacts:
        if (
                contact.feedback
                or contact.state == FAIL_STATE
        ):
            continue

        partner_user = find_user(users, user_id=contact.partner_user_id)
        text = contact_feedback_text(partner_user)
        tasks.append(BroadcastTask(
            chat_id=contact.user_id,
            text=text
        ))

    await broadcast(context.bot, tasks)
