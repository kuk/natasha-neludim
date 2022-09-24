
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
    DeleteTagsCallbackData,
    serialize_callback_data
)


def tag_user_text(user):
    if user.tags is None:
        tags = EMPTY_SYMBOL
    elif user.tags == []:
        tags = '[]'
    else:
        tags = ' '.join(f'#{_}' for _ in user.tags)

    return f'''Ссылки: {user.links or EMPTY_SYMBOL}
О себе: {user.about or EMPTY_SYMBOL}

<a href="{user_url(user.user_id)}">{user_mention(user)}</a>
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

    callback_data = DeleteTagsCallbackData(user.user_id)
    button = InlineKeyboardButton(
        text='tags=[]',
        callback_data=serialize_callback_data(callback_data)
    )
    markup.insert(button)

    return markup
