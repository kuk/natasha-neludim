
import random
from functools import partial

from aiogram.types import (
    BotCommand,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from neludim.const import (
    START_COMMAND,
    HELP_COMMAND,
    V1_COMMANDS,

    NAME_FIELD,
    CITY_FIELD,
    LINKS_FIELD,
    ABOUT_FIELD,

    EDIT_PROFILE_PREFIX,
    PARTICIPATE_PREFIX,
    FEEDBACK_PREFIX,

    CANCEL_EDIT_DATA,
    CANCEL_FEEDBACK_DATA,

    FAIL_STATE,
    CONFIRM_STATE,

    BAD_SCORE,
)
from neludim.text import (
    day_month,
    profile_text,
)
from neludim.obj import User

from .data import (
    serialize_data,
    deserialize_data,
    EditProfileData,
    ParticipateData,
    FeedbackData,
)


HAPPY_STICKERS = [
    'CAACAgIAAxkBAAEc-ftj5K0MSHy7DPqF0uwv094UGWIK4wACNgMAArrAlQVz6Uv6cxEhGy4E',
    'CAACAgIAAxkBAAEc-gNj5K05K92CtVm6cpya4bDyxyAPpQACTAMAArrAlQXYuwQVcvp2EC4E',
    'CAACAgIAAxkBAAEc-gVj5K1L5Tq9GPoglOSXul6mg9PrAAMmAwACtXHaBj4ZC4vnHBlALgQ',
    'CAACAgIAAxkBAAEc-gdj5K1ZgjZA9V6eI_GZLsyACpclgAACKQMAArVx2gbdMZInm97EAS4E',
    'CAACAgIAAxkBAAEc-gtj5K2Prjm4r9LhVJrGnnSFhGDt5QACPgMAArrAlQXle8BoEhO0GC4E',
]


#####
#
#  START
#
######


START_TEXT = '''Бот Нелюдим @neludim_bot организует random coffee для сообщества @natural_language_processing.

Пожалуйста, заполни короткую анкету. Собеседник поймёт, чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.'''

START_MARKUP = InlineKeyboardMarkup().add(
    InlineKeyboardButton(
        text='✎ Заполнить анкету',
        callback_data=serialize_data(EditProfileData())
    )
)

BOT_COMMANDS = [
    BotCommand(START_COMMAND, 'запуск'),
    BotCommand(HELP_COMMAND, 'справка'),
]


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

    await context.bot.set_my_commands(commands=BOT_COMMANDS)
    await message.answer(
        text=START_TEXT,
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

Пример:
"Закончил ШАД, работал в Яндексе в поиске. Сделал библиотеку Nile, чтобы удобно ворочать логи на Мап Редьюсе https://habr.com/ru/company/yandex/blog/332688/.

Автор проекта Наташа https://github.com/natasha. Работаю в своей Лабе https://lab.alexkuk.ru, адаптирую Наташу под задачи клиентов.

Живу в Москве в Крылатском. У нас тут мекка велоспорта. Умею сидеть на колесе и сдавать смену. Вожу экскурсии. Могу рассказать про путь от академизма к супрематизму."'''


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


async def handle_edit_input(context, message):
    user = await context.db.get_user(message.from_user.id)
    state = await context.db.get_chat_state(message.chat.id)
    data = deserialize_data(state, EditProfileData)

    if data.field == NAME_FIELD:
        user.name = message.text
    elif data.field == CITY_FIELD:
        user.city = message.text
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
    await context.db.set_chat_state(
        message.chat.id,
        state=None
    )


########
#
#   CANCEL EDIT
#
###


async def handle_cancel_edit(context, query):
    await query.answer()
    await query.message.delete()
    await context.db.set_chat_state(
        query.message.chat.id,
        state=None
    )


######
#
#   PARTICIPATE
#
#######


LATE_PARTICIPATE_TEXT = 'Не дождался твоего ответа. Бот пришлёт новое приглашение в конце недели.'
NO_PARTICIPATE_TEXT = 'Пометил, что не участвуешь во встречах. Бот пришлёт новое приглашение через неделю.'


def participate_text(context):
    return f'Пометил, что участвуешь во встречах. В понедельник {day_month(context.schedule.next_week_monday())} бот пришлёт анкету и контакт собеседника.'


async def handle_participate(context, query):
    data = deserialize_data(query.data, ParticipateData)
    current_week_index = context.schedule.current_week_index()

    await query.answer()
    user = await context.db.get_user(query.from_user.id)

    if not data.agreed:
        user.agreed_participate = None
        await context.db.put_user(user)

        await query.message.answer(text=NO_PARTICIPATE_TEXT)
        return

    if data.week_index != current_week_index + 1:
        await query.message.answer(text=LATE_PARTICIPATE_TEXT)
        return

    user.agreed_participate = context.schedule.now()
    await context.db.put_user(user)

    await query.message.reply_sticker(
        sticker=random.choice(HAPPY_STICKERS)
    )
    await query.message.answer(
        text=participate_text(context)
    )


######
#
#   FEEDBACK
#
#####


FEEDBACK_TEXT = '''Была ли встреча полезна? Дай, пожалуйста, фидбек в свободной форме.

Примеры
"Хотела узнать как работают в Сбердевайсах. Собеседник провёл экскурсию по офису и показал работу изнутри в nlp_rnd_core."

"Познакомился с ребятами из X5, Сбера. Обучались в МФТИ, ВШЭ. С одним из них стал участвовать в хаках, 2 раза заняли первое место."

"Собеседник рассказал про работу в Sber AI, MTS AI и Tinkoff AI, теперь я знаю куда не стоит идти )) Узнал инсайдерскую инфу про кредитный скоринг, жалко не успел выведать про структурированный NER."'''

BAD_FEEDACK_TEXT = '''Напиши, пожалуйста, что не понравилось.

Примеры:
- Неинтересные мне темы: компьютерные игры/биткоин
- Собеседник задержался, через 20 минут сказал что ему пора
- Бессодрежательно, просто поболтали ни о чем'''


FAIL_FEEDBACK_TEXT = '''Напиши, пожалуйста, почему встреча не состоялась.

Примеры:
- Перенесли на следующую неделю
- Договорились, собеседник перед созвоном отменил
- Написал, собеседник не ответил/перестал отвечать
- Анкета выглядит неинтересно, не стал писать
- Не было времени, не списались
- Отключил уведомления, пропустил сообщение от бота'''


CANCEL_FEEDBACK_MARKUP = InlineKeyboardMarkup().add(
    InlineKeyboardButton(
        text='✗ Не буду писать',
        callback_data=CANCEL_FEEDBACK_DATA
    )
)


async def handle_feedback(context, query):
    data = deserialize_data(query.data, FeedbackData)

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

    await query.answer()
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
    await context.db.set_chat_state(
        query.message.chat.id,
        state=None
    )


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

    await message.reply_sticker(
        sticker=random.choice(HAPPY_STICKERS)
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
- Среда - спрашивает "Получилось договориться о встрече?"
- Суббота - спрашивает "Как прошла встреча?"
- Воскресенье - спрашивает "Участвуешь на следующей неделе?"

<b>Как договориться о встрече</b>
Собеседник уже согласился участвовать во встречах и получил твою анкету. Задача участников договориться про время и место. Примеры первых сообщений:
- Привет, бот Нелюдим дал твой контакт. Когда удобно встретиться/созвониться на этой неделе? Могу в будни после 17.
- Хай, я от Нелюдима ) Ты в Сбере на Кутузовской? Можно там. Когда удобно? Могу в среду, четверг после 18.

<b>Не получилось договориться</b>
Иногда собеседник не отвечает, отказывается или переносит. По статистике 30% участников не могут договориться о встрече. С среду бот спросит "Получилось договориться о встрече?", нажми "Нет", в четверг бот пришлёт контакт нового собеседника.'''


async def handle_help(context, message):
    await message.answer(text=HELP_TEXT)


async def handle_other(context, message):
    await message.answer(text=HELP_TEXT)


#######
#
#   V1
#
####


V1_COMMANDS_TEXT = f'''20 февраля 2023 обновил интерфейс бота.

Чтобы изменить профиль, нажми /{START_COMMAND}. В остальных случаях бот сам в нужный момент пришлет нужное сообщение, подскажет куда нажимать.'''


async def handle_v1_commands(context, message):
    await message.answer(text=V1_COMMANDS_TEXT)


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
        partial(handle_v1_commands, context),
        commands=V1_COMMANDS,
    )
    context.dispatcher.register_message_handler(
        partial(handle_other, context)
    )
