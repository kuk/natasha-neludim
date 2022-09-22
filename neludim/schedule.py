
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


def week_index_thursday(index):
    return week_index_monday(index) + Timedelta(days=3)


class Schedule:
    now = Datetime.utcnow

    def current_week_index(self):
        return week_index(self.now())

    def next_week_monday(self):
        return week_index_monday(
            self.current_week_index() + 1
        )

    def current_week_thursday(self):
        return week_index_thursday(
            self.current_week_index()
        )
