
from dataclasses import dataclass
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
    THURSDAY,
    SATURDAY,
    SUNDAY,

    WEEKDAYS,
)
from . import ops


######
#  TASKS
######


# 0 0,9,17 ? * MON,WED,THU,SAT,SUN *
# msk+3, 50% users from msk, 9->12, 17->20


@dataclass
class Task:
    weekday: str
    hour: int
    op: callable

    @property
    def name(self):
        return self.op.__name__


TASKS = [
    Task(MONDAY, 0, ops.create_main_contacts),
    Task(MONDAY, 9, ops.send_main_contacts),

    Task(WEDNESDAY, 9, ops.ask_confirm_contact),

    Task(THURSDAY, 0, ops.create_extra_contacts),
    Task(THURSDAY, 9, ops.send_extra_contacts),

    Task(SATURDAY, 9, ops.ask_agree_participate),
    Task(SATURDAY, 17, ops.ask_edit_about),

    Task(SUNDAY, 17, ops.ask_contact_feedback),
    Task(SUNDAY, 17, ops.tag_users),

    Task(MONDAY, 0, ops.report_previous_week),
]


def find_tasks(tasks, datetime):
    weekday = WEEKDAYS[datetime.weekday()]
    hour = datetime.hour

    for task in tasks:
        if task.weekday == weekday and task.hour == hour:
            yield task


#####
#  APP
#####


def parse_datetime(value):
    # 2022-08-23T10:31:10.869181208Z -> 2022-08-23T10:31:10
    # fromisoformat does not support precision

    value = value[:value.index('.')]
    return Datetime.fromisoformat(value)


def parse_trigger(data):
    for item in data['messages']:
        return parse_datetime(item['event_metadata']['created_at'])


async def handle_trigger(context, request):
    data = await request.json()
    datetime = parse_trigger(data)

    tasks = find_tasks(TASKS, datetime)
    for task in tasks:
        log.info(json_msg(task=task.name))
        await task.op(context)

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
