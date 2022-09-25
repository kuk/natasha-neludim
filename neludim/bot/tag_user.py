
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from neludim.text import (
    user_url,
    user_mention,
    EMPTY_SYMBOL
)
from neludim.const import TAGS

from .callback_data import (
    AddTagCallbackData,
    ResetTagsCallbackData,
    ConfirmTagsCallbackData,
    serialize_callback_data
)


def tag_user_text(user):
    if user.tags:
        tags = ' '.join(f'#{_}' for _ in user.tags)
    else:
        tags = EMPTY_SYMBOL

    if (
            user.confirmed_tags
            and (
                not user.updated_profile
                or user.confirmed_tags > user.updated_profile
            )
    ):
        tags += ' ✓'

    return f'''{user.name or EMPTY_SYMBOL} <a href="{user_url(user.user_id)}">{user_mention(user)}</a>
Город: {user.city or EMPTY_SYMBOL}
Ссылки: {user.links or EMPTY_SYMBOL}
О себе: {user.about or EMPTY_SYMBOL}
Теги: {tags}'''


def tag_user_markup(user):
    markup = InlineKeyboardMarkup()

    for tag in TAGS:
        callback_data = AddTagCallbackData(
            user_id=user.user_id,
            tag=tag
        )
        button = InlineKeyboardButton(
            text=f'#{tag}',
            callback_data=serialize_callback_data(callback_data)
        )
        markup.insert(button)

    for text, CallbackData in [
            (EMPTY_SYMBOL, ResetTagsCallbackData),
            ('ok', ConfirmTagsCallbackData)
    ]:
        callback_data = CallbackData(user.user_id)
        button = InlineKeyboardButton(
            text=text,
            callback_data=serialize_callback_data(callback_data)
        )
        markup.insert(button)

    return markup
