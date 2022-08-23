
from datetime import (
    datetime as Datetime,
    timedelta as Timedelta
)


START_DATE = Datetime.fromisoformat('2022-08-15')
START_DATE -= Timedelta(days=START_DATE.weekday())  # monday


def week_index(datetime):
    return (datetime - START_DATE).days // 7


def week_index_monday(index):
    return START_DATE + Timedelta(days=7 * index)


def monday_sunday(monday):
    return monday + Timedelta(days=6)


class Schedule:
    now = Datetime.utcnow

    def now_week_index(self):
        return week_index(self.now())

    def next_week_monday(self):
        next_week_index = self.now_week_index() + 1
        return week_index_monday(next_week_index)
