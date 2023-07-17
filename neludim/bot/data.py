
from dataclasses import (
    dataclass,
    fields
)

from neludim.const import (
    EDIT_PROFILE_PREFIX,
    PARTICIPATE_PREFIX,
    FEEDBACK_PREFIX,
    MANUAL_MATCH_PREFIX,
)


@dataclass
class EditProfileData:
    prefix = EDIT_PROFILE_PREFIX

    field: str = None


@dataclass
class ParticipateData:
    prefix = PARTICIPATE_PREFIX

    week_index: int
    agreed: int


@dataclass
class FeedbackData:
    prefix = FEEDBACK_PREFIX

    week_index: int
    partner_user_id: int
    state: str = None
    feedback_score: str = None


@dataclass
class ManualMatchData:
    prefix = MANUAL_MATCH_PREFIX

    action: str
    user_id: int = None
    partner_user_id: int = None


def obj_annots(obj):
    return [
        (_.name, _.type)
        for _ in fields(obj)
    ]


def serialize_data(obj):
    parts = [obj.prefix]
    for name, _ in obj_annots(obj):
        value = getattr(obj, name)
        if value is None:
            part = ''
        else:
            part = str(value)
        parts.append(part)
    return ':'.join(parts)


def deserialize_data(data, cls):
    prefix, *parts = data.split(':')

    kwargs = {}
    annots = obj_annots(cls)
    for part, (name, type) in zip(parts, annots):
        if not part:
            value = None
        else:
            value = type(part)
        kwargs[name] = value
    return cls(**kwargs)
