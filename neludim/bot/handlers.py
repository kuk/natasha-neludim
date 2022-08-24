
from functools import partial

from aiogram.types import (
    BotCommand,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from neludim.const import (
    START_COMMAND,
    EDIT_INTRO_COMMAND,
    EDIT_NAME_COMMAND,
    EDIT_CITY_COMMAND,
    EDIT_LINKS_COMMAND,
    EDIT_ABOUT_COMMAND,
    CANCEL_COMMAND,
    EMPTY_COMMAND,
    PARTICIPATE_COMMAND,
    PAUSE_WEEK_COMMAND,
    PAUSE_MONTH_COMMAND,
    SHOW_CONTACT_COMMAND,
    CONFIRM_CONTACT_COMMAND,
    FAIL_CONTACT_COMMAND,
    CONTACT_FEEDBACK_COMMAND,

    EDIT_NAME_STATE,
    EDIT_CITY_STATE,
    EDIT_LINKS_STATE,
    EDIT_ABOUT_STATE,
    CONTACT_FEEDBACK_STATE,
    CONFIRM_STATE,
    FAIL_STATE,

    WEEK,
    MONTH,
)
from neludim.obj import (
    Intro,
    User,
)
from neludim.text import (
    COMMAND_DESCRIPTIONS,
    start_text,
    OTHER_TEXT,
    edit_intro_text,
    EDIT_NAME_TEXT,
    EDIT_CITY_TEXT,
    EDIT_LINKS_TEXT,
    EDIT_ABOUT_TEXT,
    TOP_CITIES,
    participate_text,
    PAUSE_TEXT,
    no_contact_text,
    show_contact_text,
    CONFIRM_CONTACT_TEXT,
    fail_contact_text,
    contact_feedback_text,
    CONTACT_FEEDBACK_OPTIONS,
    contact_feedback_state_text,
)


######
#  START
######


async def handle_start(context, message):
    user = await context.db.get_user(message.from_user.id)
    if not user:
        user = User(
            user_id=message.from_user.id,
            username=message.from_user.username,
            intro=Intro(
                name=message.from_user.full_name,
            )
        )
        await context.db.put_user(user)

    await context.bot.set_my_commands(commands=[
        BotCommand(command, description)
        for command, description
        in COMMAND_DESCRIPTIONS.items()
    ])

    text = start_text(context.schedule)
    await message.answer(text=text)


#####
#  INTRO
######


async def handle_edit_intro(context, message):
    user = await context.db.get_user(message.from_user.id)
    text = edit_intro_text(user.intro)
    await message.answer(text=text)


async def handle_edit_name(context, message):
    user = await context.db.get_user(message.from_user.id)

    markup = None
    if not user.intro.name and message.from_user.full_name:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(message.from_user.full_name)

    await message.answer(
        text=EDIT_NAME_TEXT,
        reply_markup=markup
    )
    await context.db.set_chat_state(
        message.chat.id,
        EDIT_NAME_STATE
    )


async def handle_edit_city(context, message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for city in TOP_CITIES:
        markup.insert(city)

    await message.answer(
        text=EDIT_CITY_TEXT,
        reply_markup=markup
    )
    await context.db.set_chat_state(
        message.chat.id,
        EDIT_CITY_STATE
    )


async def handle_edit_links(context, message):
    await message.answer(text=EDIT_LINKS_TEXT)
    await context.db.set_chat_state(
        message.chat.id,
        EDIT_LINKS_STATE
    )


async def handle_edit_about(context, message):
    await message.answer(text=EDIT_ABOUT_TEXT)
    await context.db.set_chat_state(
        message.chat.id,
        EDIT_ABOUT_STATE
    )


def parse_command(text):
    if text.startswith('/'):
        return text.lstrip('/')


async def handle_edit_intro_states(context, message):
    state = await context.db.get_chat_state(message.chat.id)
    user = await context.db.get_user(message.from_user.id)

    command = parse_command(message.text)
    if command != CANCEL_COMMAND:
        if command != EMPTY_COMMAND:
            value = message.text
        else:
            value = None

        if state == EDIT_NAME_STATE:
            user.intro.name = value
        elif state == EDIT_CITY_STATE:
            user.intro.city = value
        elif state == EDIT_LINKS_STATE:
            user.intro.links = value
        elif state == EDIT_ABOUT_STATE:
            user.intro.about = value

        await context.db.put_user(user)

    text = edit_intro_text(user.intro)
    await message.answer(
        text=text,
        reply_markup=ReplyKeyboardRemove()
    )
    await context.db.set_chat_state(
        message.chat.id,
        state=None
    )


######
#  PARTICIPATE/PAUSE
#######


async def handle_participate(context, message):
    user = await context.db.get_user(message.from_user.id)

    user.agreed_participate = context.schedule.now()
    user.paused = None
    user.pause_period = None

    await context.db.put_user(user)

    text = participate_text(context.schedule)
    await message.answer(text=text)


async def handle_pause(context, message):
    user = await context.db.get_user(message.from_user.id)

    user.agreed_participate = None
    user.paused = context.schedule.now()

    command = parse_command(message.text)
    if command == PAUSE_WEEK_COMMAND:
        user.pause_period = WEEK
    elif command == PAUSE_MONTH_COMMAND:
        user.pause_period = MONTH

    await context.db.put_user(user)
    await message.answer(text=PAUSE_TEXT)


######
#  CONTACT
#########


async def handle_contact(context, message):
    user = await context.db.get_user(message.from_user.id)

    if not user.partner_user_id:
        text = no_contact_text(context.schedule)
        await message.answer(text=text)
        return

    key = (
        context.schedule.current_week_index(),
        user.user_id,
        user.partner_user_id
    )
    contact = await context.db.get_contact(key)
    if not contact:
        text = no_contact_text(context.schedule)
        await message.answer(text=text)
        return

    contact.user = user
    return contact


async def handle_show_contact(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    partner_user = await context.db.get_user(contact.partner_user_id)
    text = show_contact_text(partner_user)
    await message.answer(text=text)


async def handle_confirm_contact(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    contact.state = CONFIRM_STATE
    await context.db.put_contact(contact)

    await message.answer(text=CONFIRM_CONTACT_TEXT)


async def handle_fail_contact(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    contact.state = FAIL_STATE
    await context.db.put_contact(contact)

    text = fail_contact_text(context.schedule)
    await message.answer(text=text)


async def handle_contact_feedback(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=len(CONTACT_FEEDBACK_OPTIONS)
    )
    for option in CONTACT_FEEDBACK_OPTIONS:
        markup.insert(option)

    text = contact_feedback_text(contact.user)
    await message.answer(
        text=text,
        reply_markup=markup
    )
    await context.db.set_chat_state(
        message.chat.id,
        CONTACT_FEEDBACK_STATE
    )


async def handle_contact_feedback_state(context, message):
    contact = await handle_contact(context, message)
    if not contact:
        return

    command = parse_command(message.text)
    if command != CANCEL_COMMAND:
        if command != EMPTY_COMMAND:
            contact.feedback = message.text
        else:
            contact.feedback = None

        await context.db.put_contact(contact)

    text = contact_feedback_state_text(contact.user, contact)
    await message.answer(
        text=text,
        reply_markup=ReplyKeyboardRemove()
    )
    await context.db.set_chat_state(
        message.chat.id,
        state=None
    )


######
#  OTHER
########


async def handle_other(context, message):
    await message.answer(text=OTHER_TEXT)


#######
#   SETUP
######


def setup_handlers(context):
    context.dispatcher.register_message_handler(
        partial(handle_start, context),
        commands=START_COMMAND,
    )

    context.dispatcher.register_message_handler(
        partial(handle_edit_intro, context),
        commands=EDIT_INTRO_COMMAND
    )
    context.dispatcher.register_message_handler(
        partial(handle_edit_name, context),
        commands=EDIT_NAME_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_edit_city, context),
        commands=EDIT_CITY_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_edit_links, context),
        commands=EDIT_LINKS_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_edit_about, context),
        commands=EDIT_ABOUT_COMMAND,
    )

    context.dispatcher.register_message_handler(
        partial(handle_participate, context),
        commands=PARTICIPATE_COMMAND
    )
    context.dispatcher.register_message_handler(
        partial(handle_pause, context),
        commands=[
            PAUSE_WEEK_COMMAND,
            PAUSE_MONTH_COMMAND,
        ]
    )

    context.dispatcher.register_message_handler(
        partial(handle_show_contact, context),
        commands=SHOW_CONTACT_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_confirm_contact, context),
        commands=CONFIRM_CONTACT_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_fail_contact, context),
        commands=FAIL_CONTACT_COMMAND,
    )
    context.dispatcher.register_message_handler(
        partial(handle_contact_feedback, context),
        commands=CONTACT_FEEDBACK_COMMAND,
    )

    # Every call to chat_states filter = db query. Place handlers
    # last. TODO Implement aiogram storage adapter for DynamoDB,
    # natively handle FSM

    context.dispatcher.register_message_handler(
        partial(handle_edit_intro_states, context),
        chat_states=[
            EDIT_NAME_STATE,
            EDIT_CITY_STATE,
            EDIT_LINKS_STATE,
            EDIT_ABOUT_STATE,
        ]
    )
    context.dispatcher.register_message_handler(
        partial(handle_contact_feedback_state, context),
        chat_states=CONTACT_FEEDBACK_STATE,
    )

    context.dispatcher.register_message_handler(
        partial(handle_other, context)
    )
