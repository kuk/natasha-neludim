
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
    user_mention,
    intro_text,
)
from .bot.broadcast import (
    Message,
    broadcast
)
from .schedule import week_index
from .obj import (
    Match,
    Contact,
)
from .match import gen_matches


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


def send_contact_text(user):
    return f'''Бот подобрал тебе собеседника! Его контакт в Телеграме: <a href="{user_url(user.user_id)}">{user_mention(user)}</a>.

{intro_text(user.intro)}

Пожалуйста, договоритесь про время и место встречи. Примеры, что написать:
- Привет, бот Нелюдим дал твой контакт. Когда удобно встретиться/созвониться на этой неделе?
- Хай, я от Нелюдима ) Ты в Сбере на Кутузовской? Можно там. Когда удобно?

/{CONFIRM_CONTACT_COMMAND} - договорились
/{FAIL_CONTACT_COMMAND} - не договорились/не отвечает
/{CONTACT_FEEDBACK_COMMAND} - оставить фидбек'''


def no_contact_text(schedule):
    return f'''Бот не смог подобрать тебе пару. Причины:
- Нечетное число участников. Бот исключает одного случайного.
- Мало участников на этой неделе, ты уже со всеми встречался.

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


async def ask_agree_participate(context):
    users = await context.db.read_users()
    next_week_index = context.schedule.current_week_index() + 1

    messages = []
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
        messages.append(Message(
            chat_id=user.user_id,
            text=text
        ))

    await broadcast(context.bot, messages)


async def ask_edit_intro(context):
    users = await context.db.read_users()
    next_week_index = context.schedule.current_week_index() + 1

    messages = []
    for user in users:
        if (
                user.agreed_participate
                and week_index(user.agreed_participate) + 1 == next_week_index
                and not user.intro.links
                and not user.intro.about
        ):
            messages.append(Message(
                chat_id=user.user_id,
                text=ASK_EDIT_INTRO_TEXT
            ))

    await broadcast(context.bot, messages)


async def create_contacts(context):
    users = await context.db.read_users()
    contacts = await context.db.read_contacts()
    manual_matches = await context.db.read_manual_matches()
    current_week_index = context.schedule.current_week_index()

    participate_users = []
    for user in users:
        if (
                user.agreed_participate
                and week_index(user.agreed_participate) + 1 == current_week_index
        ):
            participate_users.append(user)

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

    for match in matches:
        user_id, partner_user_id = match.key

        user = find_user(users, user_id=user_id)
        user.partner_user_id = partner_user_id

        if partner_user_id:
            partner_user = find_user(users, user_id=partner_user_id)
            partner_user.partner_user_id = user_id

    await context.db.put_contacts(contacts)
    await context.db.put_users(users)


async def send_contacts(context):
    users = await context.db.read_users()
    contacts = await context.db.read_contacts()
    contacts = find_contacts(
        contacts,
        week_index=context.schedule.current_week_index()
    )

    messages = []
    for contact in contacts:
        if not contact.partner_user_id:
            messages.append(Message(
                chat_id=contact.user_id,
                text=no_contact_text(context.schedule)
            ))

        else:
            partner_user = find_user(users, user_id=contact.partner_user_id)
            messages.append(Message(
                chat_id=contact.user_id,
                text=send_contact_text(partner_user),
            ))

    await broadcast(context.bot, messages)


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
        if contact.user_id in skip_user_ids:
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
        if contact.user_id in skip_user_ids:
            continue

        partner_user = find_user(users, user_id=contact.partner_user_id)
        text = ask_contact_feedback_text(partner_user)
        messages.append(Message(
            chat_id=contact.user_id,
            text=text
        ))

    await broadcast(context.bot, messages)
