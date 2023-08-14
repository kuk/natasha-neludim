
import random
from functools import partial

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils import exceptions

from neludim.const import (
    ADMIN_USER_ID,

    START_COMMAND,
    HELP_COMMAND,

    NAME_FIELD,
    CITY_FIELD,
    LINKS_FIELD,
    ABOUT_FIELD,

    EDIT_PROFILE_PREFIX,
    PARTICIPATE_PREFIX,
    FEEDBACK_PREFIX,
    MANUAL_MATCH_PREFIX,

    CANCEL_EDIT_DATA,
    CANCEL_FEEDBACK_DATA,

    FAIL_STATE,
    CONFIRM_STATE,

    BAD_SCORE,

    SELECT_USER_ACTION,
    SELECT_PARTNER_USER_ACTION,
    CONFIRM_ACTION,
    CANCEL_ACTION,
)
from neludim.city import (
    CITIES,
    norm_city
)
from neludim.text import (
    EMPTY_SYMBOL,
    user_mention,
    day_month,
    profile_text,
)
from neludim.obj import (
    User,
    Match
)
from neludim.schedule import week_index

from .data import (
    serialize_data,
    deserialize_data,
    EditProfileData,
    ParticipateData,
    FeedbackData,
    ManualMatchData,
)


HAPPY_STICKERS = [
    'CAACAgIAAxkBAAEc-ftj5K0MSHy7DPqF0uwv094UGWIK4wACNgMAArrAlQVz6Uv6cxEhGy4E',  # bojack clap
    'CAACAgIAAxkBAAEc-gNj5K05K92CtVm6cpya4bDyxyAPpQACTAMAArrAlQXYuwQVcvp2EC4E',  # bojack dance
    'CAACAgIAAxkBAAEc-gVj5K1L5Tq9GPoglOSXul6mg9PrAAMmAwACtXHaBj4ZC4vnHBlALgQ',  # rick like
    'CAACAgIAAxkBAAEc-gdj5K1ZgjZA9V6eI_GZLsyACpclgAACKQMAArVx2gbdMZInm97EAS4E',  # morty yes
    'CAACAgIAAxkBAAEc-gtj5K2Prjm4r9LhVJrGnnSFhGDt5QACPgMAArrAlQXle8BoEhO0GC4E',  # bojack like
]


#####
#
#  START
#
######


def start_text(context):
    return f'''Бот Нелюдим @neludim_bot организует random coffee для сообщества @natural_language_processing.

В конце недели бот спросит "Участвуешь во встречах?". Если согласишься, в понедельник {day_month(context.schedule.next_week_monday())} бот пришлёт анкету и контакт собеседника.

Пожалуйста, заполни короткую анкету. Собеседник поймёт, чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.'''


START_MARKUP = InlineKeyboardMarkup().add(
    InlineKeyboardButton(
        text='✎ Заполнить анкету',
        callback_data=serialize_data(EditProfileData())
    )
)


async def handle_start(context, message):
    user = await context.db.get_user(message.from_user.id)
    if not user:
        user = User(
            user_id=message.from_user.id,
            username=message.from_user.username,
            created=context.schedule.now(),
            name=message.from_user.full_name,
        )
        await context.db.put_user(user)

    await message.answer(
        text=start_text(context),
        reply_markup=START_MARKUP
    )


#####
#
#  EDIT PROFILE
#
######


EDIT_PROFILE_MARKUP = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton(
        text='Имя',
        callback_data=serialize_data(EditProfileData(NAME_FIELD))
    ),
    InlineKeyboardButton(
        text='Город',
        callback_data=serialize_data(EditProfileData(CITY_FIELD))
    ),
    InlineKeyboardButton(
        text='Ссылки',
        callback_data=serialize_data(EditProfileData(LINKS_FIELD))
    ),
    InlineKeyboardButton(
        text='О себе',
        callback_data=serialize_data(EditProfileData(ABOUT_FIELD))
    ),
)


async def handle_edit_profile(context, query):
    await query.answer()
    user = await context.db.get_user(query.from_user.id)
    await query.message.answer(
        text=profile_text(user),
        reply_markup=EDIT_PROFILE_MARKUP
    )


######
#
#   EDIT NAME
#
######


EDIT_NAME_TEXT = 'Напиши своё настоящее имя. Собеседник поймёт, как к тебе обращаться.'

CANCEL_EDIT_MARKUP = InlineKeyboardMarkup().add(
    InlineKeyboardButton(
        text='✗ Отменить',
        callback_data=CANCEL_EDIT_DATA
    )
)


async def handle_edit_name(context, query):
    await query.answer()
    await query.message.answer(
        text=EDIT_NAME_TEXT,
        reply_markup=CANCEL_EDIT_MARKUP
    )
    await context.db.set_chat_state(
        query.message.chat.id,
        state=serialize_data(EditProfileData(NAME_FIELD))
    )


######
#
#  EDIT CITY
#
######


EDIT_CITY_TEXT = '''Напиши город, в котором живёшь. Собеседник поймет предлагать офлайн встречу или нет.

Примеры: Москва, Санкт-Петербург, Екатеринбург, Казань, Тбилиси, Ереван, Стамбул, Амстердам, Мюнхен, Париж.'''


async def handle_edit_city(context, query):
    await query.answer()
    await query.message.answer(
        text=EDIT_CITY_TEXT,
        reply_markup=CANCEL_EDIT_MARKUP
    )
    await context.db.set_chat_state(
        query.message.chat.id,
        serialize_data(EditProfileData(CITY_FIELD))
    )


#######
#
#  EDIT LINKS
#
####


EDIT_LINKS_TEXT = '''Накидай ссылок про себя: блог, твиттер, фейсбук, канал, подкаст. Собеседник поймёт чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.

Примеры:
- http://lab.alexkuk.ru, https://github.com/kuk, https://habr.com/ru/users/alexanderkuk/
- https://www.linkedin.com/in/alexkuk/, https://vk.com/alexkuk
- http://val.maly.hk'''


async def handle_edit_links(context, query):
    await query.answer()
    await query.message.answer(
        text=EDIT_LINKS_TEXT,
        reply_markup=CANCEL_EDIT_MARKUP
    )
    await context.db.set_chat_state(
        query.message.chat.id,
        serialize_data(EditProfileData(LINKS_FIELD))
    )


######
#
#  EDIT ABOUT
#
######


EDIT_ABOUT_TEXT = '''Напиши о себе. Собеседник поймёт чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.

Что писать?
- Где учился?
- Где успел поработать? Чем занимался, самое важное/удивительное?
- Сфера интересов в NLP? Проекты, статьи.
- Личное, чем занимаешься кроме работы? Спорт, игры. Где успел пожить?

Примеры:
"Закончил ШАД, работал в Яндексе в поиске. Сделал библиотеку Nile, чтобы удобно ворочать логи на Мап Редьюсе https://habr.com/ru/company/yandex/blog/332688/.

Автор проекта Наташа https://github.com/natasha. Работаю в своей Лабе https://lab.alexkuk.ru, адаптирую Наташу под задачи клиентов."

"Училась на переводчика в ДВФУ во Владивостоке, сейчас живу в Москве. Работала в Лаборатории Касперского техническим писателем.

Только начинаю свое знакомство с NLP.  Интересно узнать от более опытных ребят про то, с чего лучше начать знакомство с этим направлением."'''


async def handle_edit_about(context, query):
    await query.answer()
    await query.message.answer(
        text=EDIT_ABOUT_TEXT,
        reply_markup=CANCEL_EDIT_MARKUP
    )
    await context.db.set_chat_state(
        query.message.chat.id,
        serialize_data(EditProfileData(ABOUT_FIELD))
    )


########
#
#   EDIT INPUT
#
#####


def warn_city_text(city, cities=CITIES):
    return f'''⚠ Не нашел город "{city}" в базе участников. Бот сравнивает названия посимвольно.

Города из базы участников: {", ".join(cities)}.

Советы:
- London -> Лондон, Moscow -> Москва
- Долгопрудный/Москва -> Москва
- Италия -> Рим, Краснодарский край -> Сочи
- Тель Авив -> Тель-Авив'''


async def handle_edit_input(context, message):
    user = await context.db.get_user(message.from_user.id)
    state = await context.db.get_chat_state(message.chat.id)
    data = deserialize_data(state, EditProfileData)

    if data.field == NAME_FIELD:
        user.name = message.text
    elif data.field == CITY_FIELD:
        user.city = norm_city(message.text)
    elif data.field == LINKS_FIELD:
        user.links = message.text
    elif data.field == ABOUT_FIELD:
        user.about = message.text

    user.updated_profile = context.schedule.now()
    await context.db.put_user(user)

    await message.answer(
        text=profile_text(user),
        reply_markup=EDIT_PROFILE_MARKUP
    )
    await context.db.reset_chat_state(message.chat.id)

    if data.field == CITY_FIELD and user.city not in CITIES:
        await message.answer(text=warn_city_text(user.city, CITIES))


########
#
#   CANCEL EDIT
#
###


async def safe_delete(message):
    try:
        await message.delete()
    except exceptions.MessageToDeleteNotFound:
        # Pressed CANCEL_EDIT_DATA twice for example
        pass


async def handle_cancel_edit(context, query):
    await query.answer()
    await safe_delete(query.message)
    await context.db.reset_chat_state(query.message.chat.id)


######
#
#   PARTICIPATE
#
#######


LATE_PARTICIPATE_TEXT = 'Не дождался твоего ответа. Бот пришлёт новое приглашение в конце недели.'
NO_PARTICIPATE_TEXT = 'Пометил, что не участвуешь во встречах. Бот пришлёт новое приглашение через неделю.'


def participate_text(context):
    return f'Пометил, что участвуешь во встречах. В понедельник {day_month(context.schedule.next_week_monday())} бот пришлёт анкету и контакт собеседника.'


NO_USERNAME_TEXT = '''Пожалуйста, заполни юзернейм в настройках Телеграма: Настройки > Изменить профиль > Имя пользователя.

Бот отправит твой юзернейм собеседнику. Без юзернейма собеседник не сможет тебе написать.'''


def no_username_markup(week_index):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text='✓ Заполнил юзернейм, участвую',
            callback_data=serialize_data(ParticipateData(week_index, agreed=1))
        )
    )


NO_ABOUT_TEXT = '''⚠ Пожалуйста, заполни "О себе" или "Ссылки" в анкете.

- Собеседник поймёт чем ты занимаешься, о чём интересно спросить.
- Алгоритм сначала метчит участников с заполненными анкетами. С пустой анкетой выше вероятность остаться без собеседника.'''

NO_ABOUT_MARKUP = InlineKeyboardMarkup().add(
    InlineKeyboardButton(
        text='✎ Заполнить анкету',
        callback_data=serialize_data(EditProfileData())
    )
)


async def handle_participate(context, query):
    data = deserialize_data(query.data, ParticipateData)
    await query.answer()

    current_week_index = context.schedule.current_week_index()
    user = await context.db.get_user(query.from_user.id)

    if not data.agreed:
        user.agreed_participate = None
        await context.db.put_user(user)

        await query.message.answer(text=NO_PARTICIPATE_TEXT)
        return

    if data.week_index != current_week_index + 1:
        await query.message.answer(text=LATE_PARTICIPATE_TEXT)
        return

    user.username = query.from_user.username
    if not user.username:
        await query.message.answer(
            text=NO_USERNAME_TEXT,
            reply_markup=no_username_markup(data.week_index)
        )
        return

    user.agreed_participate = context.schedule.now()
    await context.db.put_user(user)

    await query.message.reply_sticker(
        sticker=random.choice(HAPPY_STICKERS)
    )
    await query.message.answer(
        text=participate_text(context)
    )

    if not user.links and not user.about:
        await query.message.answer(
            text=NO_ABOUT_TEXT,
            reply_markup=NO_ABOUT_MARKUP
        )


######
#
#   FEEDBACK
#
#####


FEEDBACK_TEXT = '''Была ли встреча полезна? Дай, пожалуйста, фидбек в свободной форме.

Примеры:
"Хотела узнать как работают в Сбердевайсах. Собеседник провёл экскурсию по офису и показал работу изнутри в nlp_rnd_core."

"Собеседник рассказал про работу в Sber AI, MTS AI и Tinkoff AI, теперь я знаю куда не стоит идти )) Узнал инсайдерскую инфу про кредитный скоринг, жалко не успел выведать про структурированный NER."

Пожалуйста, напиши детали:
- "Узнал много полезных ссылок" -> "Решаю сореву про определение пола по логам, узнал ссылку на Кегл про похожее ..."
- "дал ему совет, как можно развиваться, куда копать" -> "Скинул ссылку на А, посоветовал книжку Б, рассказал свой опыт про В"'''

BAD_FEEDACK_TEXT = '''Напиши, пожалуйста, что не понравилось.

Примеры:
- Неинтересные мне темы: компьютерные игры/биткоин
- Собеседник задержался, через 20 минут сказал что ему пора
- Бессодержательно, просто поболтали ни о чем'''

FAIL_FEEDBACK_TEXT = '''Напиши, пожалуйста, почему встреча не состоялась.

Примеры:
- Перенесли на следующую неделю
- Договорились, собеседник перед созвоном отменил
- Написал, собеседник не ответил/перестал отвечать
- Анкета выглядит неинтересно, не стал писать
- Не было времени, не списались
- Отключил уведомления, пропустил сообщение от бота'''

ANYWAY_THANK_FEEDBACK_TEXT = 'В любом случае, спасибо за фидбек!'
THANK_FEEDBACK_TEXT = 'Спасибо за фидбек!'

CANCEL_FEEDBACK_MARKUP = InlineKeyboardMarkup().add(
    InlineKeyboardButton(
        text='✗ Не буду писать',
        callback_data=CANCEL_FEEDBACK_DATA
    )
)


def admin_feedback_text(user, partner_user, contact):
    return f'''feedback {user_mention(user)} -> {user_mention(partner_user)}
{contact.state} {contact.feedback_score or EMPTY_SYMBOL}

{contact.feedback_text}'''


async def handle_feedback(context, query):
    data = deserialize_data(query.data, FeedbackData)
    await query.answer()

    key = (
        data.week_index,
        query.from_user.id,
        data.partner_user_id
    )
    contact = await context.db.get_contact(key)
    contact.state = data.state
    if contact.state == CONFIRM_STATE:
        contact.feedback_score = data.feedback_score
    await context.db.put_contact(contact)

    if contact.state == FAIL_STATE:
        text = FAIL_FEEDBACK_TEXT
    elif contact.feedback_score == BAD_SCORE:
        text = BAD_FEEDACK_TEXT
    else:
        text = FEEDBACK_TEXT

    await query.message.answer(
        text=text,
        reply_markup=CANCEL_FEEDBACK_MARKUP
    )
    await context.db.set_chat_state(
        query.message.chat.id,
        serialize_data(FeedbackData(
            data.week_index,
            data.partner_user_id
        ))
    )


async def handle_cancel_feedback(context, query):
    await query.answer()
    await query.message.answer(
        text=ANYWAY_THANK_FEEDBACK_TEXT
    )
    await context.db.reset_chat_state(query.message.chat.id)


async def handle_feedback_input(context, message):
    state = await context.db.get_chat_state(message.chat.id)
    data = deserialize_data(state, FeedbackData)

    key = (
        data.week_index,
        message.from_user.id,
        data.partner_user_id
    )
    contact = await context.db.get_contact(key)
    contact.feedback_text = message.text
    await context.db.put_contact(contact)

    await message.answer(
        text=THANK_FEEDBACK_TEXT
    )
    await context.db.reset_chat_state(message.chat.id)

    user = await context.db.get_user(contact.user_id)
    partner_user = await context.db.get_user(contact.partner_user_id)
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=admin_feedback_text(user, partner_user, contact)
    )


######
#
#   MANUAL MATCH
#
######


SELECT_USER_TEXT = f'''user: {EMPTY_SYMBOL}
partner user: {EMPTY_SYMBOL}'''


def select_user_markup(users):
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


def select_partner_user_text(user):
    return f'''user: {user_mention(user)}
{profile_text(user)}

partner user: {EMPTY_SYMBOL}'''


def select_partner_user_markup(user, partner_users):
    markup = InlineKeyboardMarkup(row_width=5)
    for index, partner_user in enumerate(partner_users[:100], 1):
        button = InlineKeyboardButton(
            text=str(index),
            callback_data=serialize_data(ManualMatchData(
                action=SELECT_PARTNER_USER_ACTION,
                user_id=user.user_id,
                partner_user_id=partner_user.user_id
            ))
        )
        markup.insert(button)
    return markup


def confirm_manual_match_text(user, partner_user):
    return f'''user: {user_mention(user)}
{profile_text(user)}

partner user: {user_mention(partner_user)}
{profile_text(partner_user)}'''


def confirm_manual_match_markup(user, partner_user):
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(
            text='✓ confirm',
            callback_data=serialize_data(ManualMatchData(
                action=CONFIRM_ACTION,
                user_id=user.user_id,
                partner_user_id=partner_user.user_id
            ))
        ),
        InlineKeyboardButton(
            text='✗ cancel',
            callback_data=serialize_data(ManualMatchData(
                action=CANCEL_ACTION
            ))
        )
    )


def manual_match_text(user, partner_user):
    return f'{user_mention(user)} -> {user_mention(partner_user)}'


async def manual_match_users(context):
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
    return sorted(users, key=lambda _: _.created)


async def handle_manual_match(context, query):
    data = deserialize_data(query.data, ManualMatchData)
    await query.answer()

    if data.action == SELECT_USER_ACTION:
        user = await context.db.get_user(data.user_id)
        users = await manual_match_users(context)
        await query.message.edit_text(
            text=select_partner_user_text(user),
            reply_markup=select_partner_user_markup(user, users)
        )

    elif data.action == SELECT_PARTNER_USER_ACTION:
        user = await context.db.get_user(data.user_id)
        partner_user = await context.db.get_user(data.partner_user_id)
        await query.message.edit_text(
            text=confirm_manual_match_text(user, partner_user),
            reply_markup=confirm_manual_match_markup(user, partner_user)
        )

    elif data.action == CONFIRM_ACTION:
        user = await context.db.get_user(data.user_id)
        partner_user = await context.db.get_user(data.partner_user_id)
        match = Match(user.user_id, partner_user.user_id)
        await context.db.put_manual_match(match)
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=manual_match_text(user, partner_user)
        )

        users = await manual_match_users(context)
        await query.message.edit_text(
            text=SELECT_USER_TEXT,
            reply_markup=select_user_markup(users)
        )

    elif data.action == CANCEL_ACTION:
        users = await manual_match_users(context)
        await query.message.edit_text(
            text=SELECT_USER_TEXT,
            reply_markup=select_user_markup(users)
        )


######
#
#  HELP/OTHER
#
########


HELP_TEXT = '''Бот Нелюдим @neludim_bot организует random coffee для сообщества @natural_language_processing.

<b>Как это работает?</>
- Участник чата @natural_language_processing запускает бота, заполняет анкету. Админ чата @alexkuk читает анкеты. Алгоритм объединяет людей в пары.
- Раз в неделю бот присылает каждому участнику контакт собеседника и его анкету. Люди договариваются о времени, созваниваются или встречаются вживую.
- В конце недели бот спрашивает "Как прошла встреча?", "Будешь участвовать на следующей неделе?".

<b>Расписание</>
- Понедельник - бот присылает контакт и анкету собеседника
- Суббота - спрашивает "Как прошла встреча?"
- Воскресенье - спрашивает "Участвуешь на следующей неделе?"

<b>Как договориться о встрече</b>
Собеседник уже согласился участвовать во встречах и получил твою анкету. Задача участников договориться про время и место. Примеры первых сообщений:
- Привет, бот Нелюдим дал твой контакт. Когда удобно встретиться/созвониться на этой неделе? Могу в будни после 17.
- Хай, я от Нелюдима ) Ты в Сбере на Кутузовской? Можно там. Когда удобно? Могу в среду, четверг после 18.

<b>Не получилось договориться</b>
Иногда собеседник не отвечает, отказывается или переносит. По статистике 30% участников не могут договориться о встрече. Если согласишься участвовать на следующей неделе, бот пришлёт контакт нового собеседника.'''


async def handle_help(context, message):
    await message.answer(text=HELP_TEXT)


async def handle_other(context, message):
    await message.answer(text=HELP_TEXT)


#######
#
#   SETUP
#
######


def setup_handlers(context):
    context.dispatcher.register_message_handler(
        partial(handle_start, context),
        commands=START_COMMAND,
    )

    context.dispatcher.register_callback_query_handler(
        partial(handle_edit_profile, context),
        text=serialize_data(EditProfileData())
    )
    context.dispatcher.register_callback_query_handler(
        partial(handle_edit_name, context),
        text=serialize_data(EditProfileData(NAME_FIELD))
    )
    context.dispatcher.register_callback_query_handler(
        partial(handle_edit_city, context),
        text=serialize_data(EditProfileData(CITY_FIELD))
    )
    context.dispatcher.register_callback_query_handler(
        partial(handle_edit_links, context),
        text=serialize_data(EditProfileData(LINKS_FIELD))
    )
    context.dispatcher.register_callback_query_handler(
        partial(handle_edit_about, context),
        text=serialize_data(EditProfileData(ABOUT_FIELD))
    )
    context.dispatcher.register_callback_query_handler(
        partial(handle_cancel_edit, context),
        text=CANCEL_EDIT_DATA,
    )

    context.dispatcher.register_callback_query_handler(
        partial(handle_participate, context),
        text_startswith=PARTICIPATE_PREFIX
    )

    context.dispatcher.register_callback_query_handler(
        partial(handle_feedback, context),
        text_startswith=FEEDBACK_PREFIX
    )
    context.dispatcher.register_callback_query_handler(
        partial(handle_cancel_feedback, context),
        text=CANCEL_FEEDBACK_DATA
    )

    context.dispatcher.register_callback_query_handler(
        partial(handle_manual_match, context),
        text_startswith=MANUAL_MATCH_PREFIX
    )

    context.dispatcher.register_message_handler(
        partial(handle_help, context),
        commands=HELP_COMMAND,
    )

    # Every call to chat_states filter = db query. Place handlers
    # last. TODO Implement aiogram storage adapter for DynamoDB,
    # natively handle FSM

    context.dispatcher.register_message_handler(
        partial(handle_edit_input, context),
        chat_state_startswith=EDIT_PROFILE_PREFIX
    )
    context.dispatcher.register_message_handler(
        partial(handle_feedback_input, context),
        chat_state_startswith=FEEDBACK_PREFIX
    )

    context.dispatcher.register_message_handler(
        partial(handle_other, context)
    )
