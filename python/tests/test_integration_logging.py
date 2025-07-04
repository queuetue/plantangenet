# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

import pytest
from plantangenet.logger import Logger
from plantangenet.banker import BankerMixin, TransactionResult
from plantangenet.mixins.redis import RedisMixin
from plantangenet.mixins.nats import NatsMixin
from unittest.mock import AsyncMock, patch


class DummyBanker(BankerMixin):
    def __init__(self, logger=None):
        super().__init__()
        self._logger = logger or Logger()

    @property
    def logger(self):
        return self._logger

    def can_afford(self, amount: int) -> bool:
        return True

    def get_balance(self, *a, **kw):
        return 1000


class DummyRedis(RedisMixin):
    def __init__(self, logger=None):
        self._ocean__id = "dummy"
        self._logger = logger or Logger()

    @property
    def logger(self):
        return self._logger

    @property
    def storage_root(self):
        return "test"

    async def update_storage(self):
        pass


class DummyNats(NatsMixin):
    def __init__(self, logger=None):
        self._logger = logger or Logger()
        self._ocean_nats__client = AsyncMock()
        self._ocean_nats__connected = True

    @property
    def logger(self):
        return self._logger

    @property
    def namespace(self):
        return "test"

    @property
    def disposition(self):
        return "test"


@pytest.mark.asyncio
async def test_banker_economic_logging():
    logs = []
    logger = Logger()
    logger.on_log = lambda level, msg, ctx: logs.append((level, msg, ctx))
    banker = DummyBanker(logger)
    banker._dust_balance = 1000
    banker.deduct_dust(100, "test charge")
    assert any(l[0] == "ECONOMIC" and l[1] ==
               "plantangenet.transaction" for l in logs)


@pytest.mark.asyncio
async def test_redis_storage_logging():
    logs = []
    logger = Logger()
    logger.on_log = lambda level, msg, ctx: logs.append((level, msg, ctx))
    redis = DummyRedis(logger)
    with patch.object(redis, "_ocean__redis_client", AsyncMock(), create=True):
        await redis.set("foo", "bar")
        await redis.get("foo")
        await redis.delete("foo")
    assert any(l[0] == "STORAGE" and "SET" in l[1] for l in logs)
    assert any(l[0] == "STORAGE" and "GET" in l[1] for l in logs)
    assert any(l[0] == "STORAGE" and "DELETE" in l[1] for l in logs)


@pytest.mark.asyncio
async def test_nats_transport_logging():
    logs = []
    logger = Logger()
    logger.on_log = lambda level, msg, ctx: logs.append((level, msg, ctx))
    nats = DummyNats(logger)
    await nats.publish("foo.bar", b"baz")
    await nats.subscribe("foo.bar", AsyncMock())
    assert any(l[0] == "TRANSPORT" and "publish" in l[1] for l in logs)
    assert any(l[0] == "TRANSPORT" and "subscribe" in l[1] for l in logs)
