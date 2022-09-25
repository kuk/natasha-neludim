
from datetime import datetime as Datetime
from dataclasses import (
    dataclass,
    field,
    fields,
)

from .const import MAIN_ROUND


def obj_annots(obj):
    return [
        (_.name, _.type)
        for _ in fields(obj)
    ]


@dataclass
class Chat:
    id: int
    state: str = None


@dataclass
class User:
    user_id: int
    username: str = None
    created: Datetime = None

    agreed_participate: Datetime = None
    paused: Datetime = None
    pause_period: str = None

    name: str = None
    city: str = None
    links: str = None
    about: str = None
    updated_profile: Datetime = None

    tags: [str] = field(default_factory=list)
    confirmed_tags: Datetime = None

    partner_user_id: int = None


@dataclass
class Contact:
    week_index: int
    user_id: int

    # no partner for this week: odd participants
    partner_user_id: int = None

    round: str = MAIN_ROUND
    state: str = None
    feedback: str = None

    @property
    def key(self):
        if self.partner_user_id:
            return (
                self.week_index,
                self.user_id,
                self.partner_user_id
            )
        else:
            return (
                self.week_index,
                self.user_id
            )


@dataclass
class Match:
    user_id: int
    partner_user_id: int

    @property
    def key(self):
        return (self.user_id, self.partner_user_id)
