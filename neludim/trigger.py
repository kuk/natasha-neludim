
from datetime import datetime as Datetime
from functools import partial

from aiohttp import web

from neludim.const import ADMIN_USER_ID


######
#  PARSE
#####


# {
#     "messages": [
# 	 {
# 	     "event_metadata": {
# 		 "event_type": "yandex.cloud.events.serverless.triggers.TimerMessage",
# 		 "created_at": "2022-08-23T10:31:10.869181208Z",
# 		 "folder_id": "b1gvn9housafmd323832"
# 	     },
# 	     "trigger_id": "a1s8tlitsoh648k1sun5"
# 	 }
#     }


def parse_datetime(value):
    # 2022-08-23T10:31:10.869181208Z -> 2022-08-23T10:31:10
    # fromisoformat does not support precision

    value = value[:value.index('.')]
    return Datetime.fromisoformat(value)


def parse_trigger(data):
    for item in data['messages']:
        return parse_datetime(item['event_metadata']['created_at'])


#######
#  SCHEDULE
#######


MONDAY = 'monday'
TUESDAY = 'tuesday'
WEDNESDAY = 'wednesday'
THURSDAY = 'thursday'
FRIDAY = 'friday'
SATURDAY = 'saturday'
SUNDAY = 'sunday'

WEEKDAYS = [
    MONDAY,
    TUESDAY,
    WEDNESDAY,
    THURSDAY,
    FRIDAY,
    SATURDAY,
    SUNDAY
]


# 0 0,9,17 ? * MON,WED,SAT,SUN *
# msk+3, 50% users from msk, 9->12, 17->20


SCHEDULE = {
    (MONDAY, 0): 'create_contacts',
    (MONDAY, 9): 'send_contacts',

    (WEDNESDAY, 9): 'ask_confirm_contact',
    (SATURDAY, 9): 'ask_agree_participate',
    (SATURDAY, 17): 'ask_edit_intro',
    (SUNDAY, 17): 'ask_contact_feedback',
}


#######
#  APP
#######


async def handle_trigger(context, request):
    data = await request.json()
    datetime = parse_trigger(data)

    weekday = WEEKDAYS[datetime.weekday()]
    hour = datetime.hour
    op = SCHEDULE.get((weekday, hour))
    if not op:
        return

    text = f'TRIGGER {datetime} {op}'
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=text
    )


async def on_startup(context, _):
    await context.db.connect()


async def on_shutdown(context, _):
    await context.db.close()


def start_webhook(context):
    app = web.Application()

    app.add_routes([
        web.post('/', partial(handle_trigger, context))
    ])

    app.on_startup.append(partial(on_startup, context))
    app.on_shutdown.append(partial(on_shutdown, context))

    web.run_app(
        app,
        print=None
    )
