
import asyncio

import pytest

from neludim.db import DB
from neludim.tests.fake import (
    FakeContext,
    fake_setup
)


# If put in test_db.py raises something about asyncio close
# https://stackoverflow.com/questions/61022713/pytest-asyncio-has-a-closed-event-loop-but-only-when-running-all-tests


@pytest.fixture(scope='session')
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope='session')
async def db():
    db = DB()
    await db.connect()
    yield db
    await db.close()


@pytest.fixture(scope='function')
def context():
    context = FakeContext()
    fake_setup(context)

    return context
