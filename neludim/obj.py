
from datetime import datetime as Datetime
from dataclasses import (
    dataclass,
    fields,
)


def obj_annots(obj):
    for field in fields(obj):
        yield field.name, field.type


@dataclass
class Chat:
    id: int
    state: str = None


@dataclass
class Intro:
    name: str = None
    city: str = None
    links: str = None
    about: str = None


@dataclass
class User:
    user_id: int
    username: str = None

    agreed_participate: Datetime = None
    paused: Datetime = None
    pause_period: str = None

    intro: Intro = None

    partner_user_id: int = None


@dataclass
class Contact:
    week_index: int
    user_id: int
    partner_user_id: int

    state: str = None
    feedback: str = None

    @property
    def key(self):
        return (
            self.week_index,
            self.user_id,
            self.partner_user_id
        )
