
from dataclasses import is_dataclass
from datetime import datetime as Datetime
from contextlib import AsyncExitStack

import aiobotocore.session

from .const import (
    DYNAMO_ENDPOINT,
    AWS_KEY_ID,
    AWS_KEY,

    N, S, M, SS
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
#
#  OPS
#
#####


# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html


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


async def dynamo_put(client, table, item):
    await client.put_item(
        TableName=table,
        Item=item
    )


async def dynamo_delete(client, table, key_name, key_type, key_value):
    await client.delete_item(
        TableName=table,
        Key={
            key_name: {
                key_type: str(key_value)
            }
        }
    )


async def dynamo_scan(client, table):
    pager = client.get_paginator('scan')
    responses = pager.paginate(
        TableName=table
    )
    items = []
    async for response in responses:
        items.extend(response['Items'])
    return items


def iter_batches(items, max_size=25):
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= max_size:
            yield batch
            batch = []
    if batch:
        yield batch


async def dynamo_batch_put(client, table, items):
    for batch in iter_batches(items):
        await client.batch_write_item(
            RequestItems={
                table: [
                    {
                        'PutRequest': {
                            'Item': _
                        }
                    }
                    for _ in batch
                ]
            }
        )


async def dynamo_batch_delete(client, table, key_name, key_type, key_values):
    for batch in iter_batches(key_values):
        await client.batch_write_item(
            RequestItems={
                table: [
                    {
                        'DeleteRequest': {
                            'Key': {
                                key_name: {
                                    key_type: str(_)
                                }
                            }
                        }
                    }
                    for _ in batch
                ]
            }
        )


######
#
#   DE/SERIALIZE
#
####


def dynamo_type(annot):
    if annot == int:
        return N
    elif annot in (str, Datetime):
        return S
    elif annot == [str]:
        return SS
    elif is_dataclass(annot):
        return M


def dynamo_deserialize_value(value, annot):
    if annot == int:
        return int(value)
    elif annot in (str, [str]):
        return value
    elif annot == Datetime:
        return Datetime.fromisoformat(value)
    elif is_dataclass(annot):
        return dynamo_deserialize_item(value, annot)


def dynamo_serialize_value(value, annot):
    if annot == int:
        return str(value)
    elif annot in (str, [str]):
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


# On DynamoDB partition key
# https://aws.amazon.com/ru/blogs/database/choosing-the-right-dynamodb-partition-key/


def dynamo_serialize_key(parts):
    return '#'.join(
        str(_) for _ in parts
    )
