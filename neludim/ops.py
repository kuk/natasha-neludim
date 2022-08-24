
from .const import (
    CONFIRM_STATE,
    FAIL_STATE
)
from .text import (
    broadcast_confirm_contact_text
)

from .bot.broadcast import (
    BroadcastTask,
    broadcast
)


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


async def broadcast_confirm_contact(context):
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
        text = broadcast_confirm_contact_text(partner_user)
        tasks.append(BroadcastTask(
            chat_id=contact.user_id,
            text=text
        ))

    await broadcast(context.bot, tasks)
