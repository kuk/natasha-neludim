
from aiogram.dispatcher.filters import BoundFilter


class ChatStateFilter(BoundFilter):
    context = None
    key = 'chat_state_startswith'

    def __init__(self, chat_state_startswith):
        self.chat_state_startswith = chat_state_startswith

    async def check(self, obj):
        state = await self.context.db.get_chat_state(obj.chat.id)
        return state and state.startswith(self.chat_state_startswith)


def setup_filters(context):
    ChatStateFilter.context = context
    context.dispatcher.filters_factory.bind(ChatStateFilter)
