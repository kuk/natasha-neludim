
from dataclasses import (
    dataclass,
    fields
)

from neludim.const import (
    ADD_TAG_PREFIX,
    DELETE_TAGS_PREFIX,
)


@dataclass
class AddTagCallbackData:
    prefix = ADD_TAG_PREFIX

    user_id: int
    tag: str


@dataclass
class DeleteTagsCallbackData:
    prefix = DELETE_TAGS_PREFIX

    user_id: int


def obj_annots(obj):
    for field in fields(obj):
        yield field.name, field.type


def deserialize_callback_data(data, cls):
    prefix, *parts = data.split(':')

    kwargs = {}
    annots = obj_annots(cls)
    for part, (name, annot) in zip(parts, annots):
        kwargs[name] = annot(part)
    return cls(**kwargs)


def serialize_callback_data(obj):
    parts = [obj.prefix]
    for name, _ in obj_annots(obj):
        value = getattr(obj, name)
        parts.append(str(value))
    return ':'.join(parts)
