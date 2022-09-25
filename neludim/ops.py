
from .const import (
    ADMIN_USER_ID,

    HELP_COMMAND,
    PARTICIPATE_COMMAND,
    PAUSE_WEEK_COMMAND,
    PAUSE_MONTH_COMMAND,
    EDIT_LINKS_COMMAND,
    EDIT_ABOUT_COMMAND,
    CONFIRM_CONTACT_COMMAND,
    FAIL_CONTACT_COMMAND,
    CONTACT_FEEDBACK_COMMAND,

    CONFIRM_STATE,
    FAIL_STATE,

    MAIN_ROUND,
    EXTRA_ROUND,

    WEEK_PERIOD,
    MONTH_PERIOD,
)
from .text import (
    day_month,
    user_url,
    user_mention,
    intro_text,
)
from .bot.broadcast import (
    Message,
    broadcast
)
from .bot.tag_user import (
    tag_user_text,
    tag_user_markup
)
from .schedule import week_index
from .obj import (
    Match,
    Contact,
)
from .match import gen_matches
from .report import (
    gen_report,
    report_text
)


#######
#  TEXT
####


def ask_agree_participate_text(schedule):
    return f'''Участвуешь во встречах на следующей неделе? Если дашь согласие, в понедельник {day_month(schedule.next_week_monday())} бот пришлёт анкету и контакт собеседника.

/{PARTICIPATE_COMMAND} - участвовать
/{PAUSE_WEEK_COMMAND} - пауза на неделю
/{PAUSE_MONTH_COMMAND} - пауза на месяц

Бот просит подтверждать участие каждую неделю. Подбирает собеседника только из тех, кто согласился. Это уменьшает число несостоявшихся встреч.'''


ASK_EDIT_ABOUT_TEXT = f'''Заполни, пожалуйста, ссылки /{EDIT_LINKS_COMMAND} или "о себе" /{EDIT_ABOUT_COMMAND}.

Собеседник поймёт чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.'''


# MAYBE TODO
# Предлагаю тебе заполнить новый раздел "о себе" в анкете /edit_about.
# Упростит задачу собеседнику, быстрее поймёт чем ты занимаешься, не придётся ходить по ссылкам.


def send_contact_text(user):
    return f'''Бот подобрал тебе собеседника! Его контакт в Телеграме: <a href="{user_url(user.user_id)}">{user_mention(user)}</a>. Пожалуйста, договоритесь про время и место встречи.

{intro_text(user)}

/{CONFIRM_CONTACT_COMMAND} - договорились
/{FAIL_CONTACT_COMMAND} - не договорились/не отвечает
/{HELP_COMMAND} - советы, как договориться о встрече'''


def no_contact_text(schedule, round):
    if round == MAIN_ROUND:
        return f'''Бот не смог подобрать тебе собеседника. Причины:
- Нечетное число участников. Бот исключает одного случайного.
- Мало участников на этой неделе, ты уже со всеми встречался.

Бот повторит попытку в четверг {day_month(schedule.current_week_thursday())}. По статистике у 15-30% участников не получается договориться о встрече, бот подберет собеседника среди них.'''

    elif round == EXTRA_ROUND:
        return '''Бот не смог подобрать тебе собеседника. Причины:
- Нечетное число участников. Бот исключает одного случайного.
- На этой неделе у многих получилось договориться о встрече, с остальными ты уже встречался.

Участвуешь на следующей неделе? Если дашь согласие, в понедельник {day_month(schedule.next_week_monday())} бот пришлёт анкету и контакт собеседника.

/{PARTICIPATE_COMMAND} - участвовать
/{PAUSE_WEEK_COMMAND} - пауза на неделю
/{PAUSE_MONTH_COMMAND} - пауза на месяц'''


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
#   OPS
######


def find_contacts(contacts, week_index=None):
    for contact in contacts:
        if week_index is not None and contact.week_index == week_index:
            yield contact


def find_user(users, user_id=None, username=None, name=None):
    for user in users:
        if (
                user_id is not None and user.user_id == user_id
                or username is not None and user.username == username
                or name is not None and user.name == name
        ):
            return user


async def ask_agree_participate(context):
    users = await context.db.read_users()
    next_week_index = context.schedule.current_week_index() + 1

    messages = []
    for user in users:
        if user.paused:
            if user.pause_period == WEEK_PERIOD:
                offset = 1
            elif user.pause_period == MONTH_PERIOD:
                offset = 4

            if next_week_index <= week_index(user.paused) + offset:
                continue

        if (
                user.agreed_participate
                and week_index(user.agreed_participate) + 1 == next_week_index
        ):
            continue

        text = ask_agree_participate_text(context.schedule)
        messages.append(Message(
            chat_id=user.user_id,
            text=text
        ))

    await broadcast(context.bot, messages)


async def ask_edit_about(context):
    users = await context.db.read_users()
    next_week_index = context.schedule.current_week_index() + 1

    messages = []
    for user in users:
        if (
                user.agreed_participate
                and week_index(user.agreed_participate) + 1 == next_week_index
                and not user.links
                and not user.about
        ):
            messages.append(Message(
                chat_id=user.user_id,
                text=ASK_EDIT_ABOUT_TEXT
            ))

    await broadcast(context.bot, messages)


def main_participate_users(users, current_week_index):
    for user in users:
        if (
                user.agreed_participate
                and week_index(user.agreed_participate) + 1 == current_week_index
        ):
            yield user


def extra_participate_users(users, contacts, current_week_index):
    user_ids = set()
    for contact in contacts:
        if (
                contact.week_index == current_week_index
                and (contact.state == FAIL_STATE or contact.partner_user_id is None)
        ):
            user_ids.add(contact.user_id)

    for user in users:
        if (
                user.user_id in user_ids

                # In case /fail_contact + /pause_week, skip thursday
                # match and skip next week
                and user.agreed_participate
        ):
            yield user


async def create_contacts(context, round):
    users = await context.db.read_users()
    contacts = await context.db.read_contacts()
    manual_matches = await context.db.read_manual_matches()
    current_week_index = context.schedule.current_week_index()

    if round == MAIN_ROUND:
        participate_users = list(main_participate_users(users, current_week_index))

    elif round == EXTRA_ROUND:
        participate_users = list(extra_participate_users(users, contacts, current_week_index))

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
            round=round,
            user_id=user_id,
            partner_user_id=partner_user_id
        ))

        if partner_user_id:
            contacts.append(Contact(
                week_index=current_week_index,
                round=round,
                user_id=partner_user_id,
                partner_user_id=user_id
            ))

    if round == MAIN_ROUND:
        for user in users:
            user.partner_user_id = None

    for match in matches:
        user_id, partner_user_id = match.key

        user = find_user(users, user_id=user_id)
        user.partner_user_id = partner_user_id

        if partner_user_id:
            partner_user = find_user(users, user_id=partner_user_id)
            partner_user.partner_user_id = user_id

    await context.db.put_contacts(contacts)
    await context.db.put_users(users)


async def create_main_contacts(context):
    await create_contacts(context, MAIN_ROUND)


async def create_extra_contacts(context):
    await create_contacts(context, EXTRA_ROUND)


async def send_contacts(context, round):
    users = await context.db.read_users()
    contacts = await context.db.read_contacts()
    contacts = find_contacts(
        contacts,
        week_index=context.schedule.current_week_index()
    )

    messages = []
    for contact in contacts:
        if contact.round != round:
            continue

        if not contact.partner_user_id:
            messages.append(Message(
                chat_id=contact.user_id,
                text=no_contact_text(context.schedule, round)
            ))

        else:
            partner_user = find_user(users, user_id=contact.partner_user_id)
            messages.append(Message(
                chat_id=contact.user_id,
                text=send_contact_text(partner_user),
            ))

    await broadcast(context.bot, messages)


async def send_main_contacts(context):
    await send_contacts(context, MAIN_ROUND)


async def send_extra_contacts(context):
    await send_contacts(context, EXTRA_ROUND)


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

    messages = []
    for contact in contacts:
        if contact.user_id in skip_user_ids or not contact.partner_user_id:
            continue

        partner_user = find_user(users, user_id=contact.partner_user_id)
        text = ask_confirm_contact_text(partner_user)
        messages.append(Message(
            chat_id=contact.user_id,
            text=text
        ))

    await broadcast(context.bot, messages)


async def ask_contact_feedback(context):
    users = await context.db.read_users()

    contacts = await context.db.read_contacts()
    contacts = list(find_contacts(
        contacts,
        week_index=context.schedule.current_week_index()
    ))

    skip_user_ids = set()
    for contact in contacts:
        if contact.feedback:
            skip_user_ids.add(contact.user_id)

        if contact.state == FAIL_STATE:
            skip_user_ids.add(contact.user_id)
            skip_user_ids.add(contact.partner_user_id)

    messages = []
    for contact in contacts:
        if contact.user_id in skip_user_ids or not contact.partner_user_id:
            continue

        partner_user = find_user(users, user_id=contact.partner_user_id)
        text = ask_contact_feedback_text(partner_user)
        messages.append(Message(
            chat_id=contact.user_id,
            text=text
        ))

    await broadcast(context.bot, messages)


async def report_previous_week(context):
    users = await context.db.read_users()
    contacts = await context.db.read_contacts()
    previous_week_index = context.schedule.current_week_index() - 1

    records = gen_report(
        users, contacts,
        week_index=previous_week_index
    )
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=report_text(records, html=True)
    )


async def tag_users(context):
    users = await context.db.read_users()

    for user in users:
        if (
                user.updated_profile
                and (
                    not user.confirmed_tags
                    or user.confirmed_tags < user.updated_profile
                )
        ):
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=tag_user_text(user),
                reply_markup=tag_user_markup(user)
            )
