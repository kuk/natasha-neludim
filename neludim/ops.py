
from .const import (
    PARTICIPATE_COMMAND,
    PAUSE_WEEK_COMMAND,
    PAUSE_MONTH_COMMAND,
    CONFIRM_CONTACT_COMMAND,
    FAIL_CONTACT_COMMAND,
    CONTACT_FEEDBACK_COMMAND,

    CONFIRM_STATE,
    FAIL_STATE,

    WEEK,
    MONTH,
)
from .text import (
    day_month,
    user_url,
    user_mention
)
from .schedule import week_index
from .bot.broadcast import (
    BroadcastTask,
    broadcast
)


#######
#
#  TEXT
#
####


def ask_agree_participate_text(schedule):
    return f'''Участвуешь во встречах на следующей неделе? Если дашь согласие, в понедельник {day_month(schedule.next_week_monday())} бот пришлёт анкету и контакт собеседника.

/{PARTICIPATE_COMMAND} - участвовать
/{PAUSE_WEEK_COMMAND} - пауза на неделю
/{PAUSE_MONTH_COMMAND} - пауза на месяц

Бот просит подтверждать участие каждую неделю. Подбирает собеседника только из тех, кто согласился. Это уменьшает число несостоявшихся встреч.'''


ASK_EDIT_INTRO_TEXT = '''Заполни, пожалуйста, профиль: ссылки /edit_links или "о себе" /edit_about.

Собеседник поймёт чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.'''


# MAYBE TODO
# Предлагаю тебе заполнить новый раздел "о себе" в анкете /edit_about.
# Упростит задачу собеседнику, быстрее поймёт чем ты занимаешься, не придётся ходить по ссылкам.


def ask_confirm_contact_text(user):
    return f'''Получилось договориться с <a href="{user_url(user.user_id)}">{user_mention(user)}</a> о встрече?

/{CONFIRM_CONTACT_COMMAND} - да, договорились
/{FAIL_CONTACT_COMMAND} - не договорились/не отвечает'''


def ask_contact_feedback_text(user):
    return f'''Оставь, пожалуйста, фидбек о встрече с <a href="{user_url(user.user_id)}">{user_mention(user)}</a>.

/{CONTACT_FEEDBACK_COMMAND} - оставить фидбек
/{FAIL_CONTACT_COMMAND} - встреча не состоялась

Бот просит оценить встречу от 1 до 5, использует фидбек, чтобы лучше подбирать собеседников.'''


######
#
#   OPS
#
######


async def ask_agree_participate(context):
    users = await context.db.read_users()
    next_week_index = context.schedule.current_week_index() + 1

    tasks = []
    for user in users:
        if user.paused:
            if user.pause_period == WEEK:
                offset = 1
            elif user.pause_period == MONTH:
                offset = 4

            if next_week_index <= week_index(user.paused) + offset:
                continue

        if (
                user.agreed_participate
                and week_index(user.agreed_participate) + 1 == next_week_index
        ):
            continue

        text = ask_agree_participate_text(context.schedule)
        tasks.append(BroadcastTask(
            chat_id=user.user_id,
            text=text
        ))

    await broadcast(context.bot, tasks)


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


async def ask_edit_intro(context):
    users = await context.db.read_users()
    next_week_index = context.schedule.current_week_index() + 1

    tasks = []
    for user in users:
        if (
                user.agreed_participate
                and week_index(user.agreed_participate) + 1 == next_week_index
                and not user.intro.links
                and not user.intro.about
        ):
            tasks.append(BroadcastTask(
                chat_id=user.user_id,
                text=ASK_EDIT_INTRO_TEXT
            ))

    await broadcast(context.bot, tasks)


async def ask_confirm_contact(context):
    users = await context.db.read_users()

    contacts = await context.db.read_contacts()
    contacts = list(find_contacts(
        contacts,
        week_index=context.schedule.current_week_index()
    ))

    skip_user_ids = set()
    for contact in contacts:
        # If skip a->b, also skip b->a
        if (
                contact.state in (CONFIRM_STATE, FAIL_STATE)
                or contact.feedback
        ):
            skip_user_ids.add(contact.user_id)
            skip_user_ids.add(contact.partner_user_id)

    tasks = []
    for contact in contacts:
        if contact.user_id in skip_user_ids:
            continue

        partner_user = find_user(users, user_id=contact.partner_user_id)
        text = ask_confirm_contact_text(partner_user)
        tasks.append(BroadcastTask(
            chat_id=contact.user_id,
            text=text
        ))

    await broadcast(context.bot, tasks)


async def ask_contact_feedback(context):
    users = await context.db.read_users()

    contacts = await context.db.read_contacts()
    contacts = find_contacts(
        contacts,
        week_index=context.schedule.current_week_index()
    )

    tasks = []
    for contact in contacts:
        if (
                contact.feedback
                or contact.state == FAIL_STATE
        ):
            continue

        partner_user = find_user(users, user_id=contact.partner_user_id)
        text = ask_contact_feedback_text(partner_user)
        tasks.append(BroadcastTask(
            chat_id=contact.user_id,
            text=text
        ))

    await broadcast(context.bot, tasks)
