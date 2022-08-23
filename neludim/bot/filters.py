
from aiogram.dispatcher.filters import BoundFilter


class ChatStatesFilter(BoundFilter):
    context = None
    key = 'chat_states'

    def __init__(self, chat_states):
        if not isinstance(chat_states, list):
            chat_states = [chat_states]
        self.chat_states = chat_states

    async def check(self, obj):
        state = await self.context.db.get_chat_state(obj.chat.id)
        return state in self.chat_states


def setup_filters(context):
    ChatStatesFilter.context = context
    context.dispatcher.filters_factory.bind(ChatStatesFilter)
