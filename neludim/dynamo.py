
from dataclasses import is_dataclass
from datetime import datetime as Datetime
from contextlib import AsyncExitStack

import aiobotocore.session

from .const import (
    DYNAMO_ENDPOINT,
    AWS_KEY_ID,
    AWS_KEY,

    BOOL,
    N, S, M
)
from .obj import obj_annots


async def dynamo_client():
    session = aiobotocore.session.get_session()
    manager = session.create_client(
        'dynamodb',

        # Always ru-central1 for YC
        # https://cloud.yandex.ru/docs/ydb/docapi/tools/aws-setup
        region_name='ru-central1',

        endpoint_url=DYNAMO_ENDPOINT,
        aws_access_key_id=AWS_KEY_ID,
        aws_secret_access_key=AWS_KEY,
    )

    # https://github.com/aio-libs/aiobotocore/discussions/955
    exit_stack = AsyncExitStack()
    client = await exit_stack.enter_async_context(manager)
    return exit_stack, client


######
#  OPS
#####


async def dynamo_scan(client, table):
    response = await client.scan(
        TableName=table
    )
    return response['Items']


async def dynamo_put(client, table, item):
    await client.put_item(
        TableName=table,
        Item=item
    )


async def dynamo_get(client, table, key_name, key_type, key_value):
    response = await client.get_item(
        TableName=table,
        Key={
            key_name: {
                key_type: str(key_value)
            }
        }
    )
    return response.get('Item')


async def dynamo_delete(client, table, key_name, key_type, key_value):
    await client.delete_item(
        TableName=table,
        Key={
            key_name: {
                key_type: str(key_value)
            }
        }
    )


######
#   DE/SERIALIZE
####


def dynamo_type(annot):
    if annot == bool:
        return BOOL
    elif annot == int:
        return N
    elif annot in (str, Datetime):
        return S
    elif is_dataclass(annot):
        return M


def dynamo_deserialize_value(value, annot):
    if annot == bool:
        return value
    elif annot == int:
        return int(value)
    elif annot == str:
        return value
    elif annot == Datetime:
        return Datetime.fromisoformat(value)
    elif is_dataclass(annot):
        return dynamo_deserialize_item(value, annot)


def dynamo_serialize_value(value, annot):
    if annot == bool:
        return value
    elif annot == int:
        return str(value)
    elif annot == str:
        return value
    elif annot == Datetime:
        return value.isoformat()
    elif is_dataclass(annot):
        return dynamo_serialize_item(value)


def dynamo_deserialize_item(item, cls):
    kwargs = {}
    for name, annot in obj_annots(cls):
        if name in item:
            type = dynamo_type(annot)
            value = item[name][type]
            value = dynamo_deserialize_value(value, annot)
        else:
            value = None
        kwargs[name] = value
    return cls(**kwargs)


def dynamo_serialize_item(obj):
    item = {}
    for name, annot in obj_annots(obj):
        value = getattr(obj, name)
        if value is not None:
            value = dynamo_serialize_value(value, annot)
            type = dynamo_type(annot)
            item[name] = {type: value}
    return item


#####
#  KEY
######


# On DynamoDB partition key
# https://aws.amazon.com/ru/blogs/database/choosing-the-right-dynamodb-partition-key/


def dynamo_key(parts):
    return '#'.join(
        str(_) for _ in parts
    )
