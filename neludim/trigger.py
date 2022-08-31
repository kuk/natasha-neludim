
from datetime import datetime as Datetime
from functools import partial

from aiohttp import web

from .log import (
    log,
    json_msg,
)
from .const import (
    MONDAY,
    WEDNESDAY,
    SATURDAY,
    SUNDAY,

    WEEKDAYS,
)
from .ops import (
    create_contacts,
    send_contacts,
    ask_confirm_contact,
    ask_agree_participate,
    ask_edit_intro,
    ask_contact_feedback,
)


######
#  PARSE
#####


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


# 0 0,9,17 ? * MON,WED,SAT,SUN *
# msk+3, 50% users from msk, 9->12, 17->20


SCHEDULE = {
    (MONDAY, 0): create_contacts,
    (MONDAY, 9): send_contacts,
    (WEDNESDAY, 9): ask_confirm_contact,
    (SATURDAY, 9): ask_agree_participate,
    (SATURDAY, 17): ask_edit_intro,
    (SUNDAY, 17): ask_contact_feedback,
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
    if op:
        log.info(json_msg(op=op.__name__))
        await op(context)

    return web.Response()


async def on_startup(context, _):
    await context.db.connect()


async def on_shutdown(context, _):
    await context.db.close()


def build_app(context):
    app = web.Application()

    app.add_routes([
        web.post('/', partial(handle_trigger, context))
    ])

    app.on_startup.append(partial(on_startup, context))
    app.on_shutdown.append(partial(on_shutdown, context))

    return app


def start_webhook(context):
    web.run_app(
        build_app(context),
        print=None
    )
