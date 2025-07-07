# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
import asyncio
import json
import redis.asyncio as Redis
from typing import Any, List, Optional
from plantangenet.omni.mixins.storage import StorageMixin
from random import randint


class RedisMixin(StorageMixin):
    """
    A mixin for Redis operations, providing basic key-value store functionality.
    This mixin is designed to be used with an async Redis client.
    It supports setting, getting, deleting keys, checking existence, and listing keys.
    It also provides a TTL (time-to-live) for keys, which defaults to 61 seconds.
    """
    _ocean__redis_ttl: int = 61
    _ocean__id: str
    _storage__ttl = 600
    _storage_prefix: str = "plantangenet"

    def __init__(self, ttl: Optional[int] = None, prefix: Optional[str] = None):
        self._ocean__redis_client: Optional[Redis.Redis] = None
        if self._ocean__id is None:
            raise ValueError("StorageMixin requires an _ocean__id to be set.")
        if ttl is not None and ttl <= 0:
            self._storage__ttl = ttl
        if prefix is not None:
            self._storage_prefix = prefix

    @property
    def storage_prefix(self) -> str:
        """
        Get the storage prefix for the peer.
        :return: The storage prefix.
        """
        return self._storage_prefix

    @property
    @abstractmethod
    def logger(self) -> Any:
        """Return the logger instance for this peer."""
        raise NotImplementedError(
            "Logger must be implemented in the subclass."
        )

    async def setup_storage(self, urls: list[str]) -> None:
        """Setup Redis storage with resilient connection handling."""
        max_retries = 3
        base_delay = 1.0
        retry_count = 0

        while self._ocean__redis_client is None and retry_count < max_retries:
            try:
                url = urls[randint(0, len(urls) - 1)]
                if retry_count > 0:
                    self.logger.info(
                        f"Attempting Redis connection (attempt {retry_count + 1}/{max_retries})")

                # Try to connect with timeout
                self._ocean__redis_client = Redis.from_url(
                    url,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    retry_on_timeout=False
                )

                # Test the connection with a simple ping
                await asyncio.wait_for(self._ocean__redis_client.ping(), timeout=5.0)
                if retry_count > 0:
                    self.logger.info(
                        "Redis connection established successfully")
                return  # Success, exit the method

            except (ConnectionError, OSError, asyncio.TimeoutError) as e:
                retry_count += 1
                if self._ocean__redis_client:
                    try:
                        await self._ocean__redis_client.close()
                    except:
                        pass
                    self._ocean__redis_client = None

                if retry_count < max_retries:
                    delay = base_delay * (2 ** (retry_count - 1))
                    self.logger.warning(
                        f"Redis connection failed (attempt {retry_count}/{max_retries}): {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"Redis connection failed after {max_retries} attempts: {e}. "
                        "Continuing in offline mode."
                    )

            except Exception as e:
                retry_count += 1
                if self._ocean__redis_client:
                    try:
                        await self._ocean__redis_client.close()
                    except:
                        pass
                    self._ocean__redis_client = None
                self.logger.info("Failed to connect to Redis.")

                if retry_count >= max_retries:
                    self.logger.error(
                        "Maximum Redis connection retries exceeded. Continuing in offline mode.")
                    break

    async def teardown_storage(self):
        if self._ocean__redis_client:
            await self._ocean__redis_client.close()
            self._ocean__redis_client = None

    async def get(self, key: str, actor=None) -> Optional[str]:
        if not self._ocean__redis_client:
            raise RuntimeError("Redis client is not connected")
        if actor:
            key = f"{self.storage_root}:actors:{actor}:{key}"
        else:
            key = f"{self.storage_root}:peer:{key}"
        value = await self._ocean__redis_client.get(key)
        self.logger.storage(
            f"Redis GET {key}",
            context={"key": key, "operation": "get",
                     "result": value is not None}
        )
        return value

    async def set(self, key: str, value: Any, nx: bool = False, ttl: Optional[int] = None, actor=None) -> Optional[list]:
        """
           Set a value in the store with a TTL.
           :param key: The key under which to store the value.
           :param value: The value to store.
           :param nx: If True, set the key only if it does not already exist.
           :param ttl: Time-to-live in seconds. Defaults to 61 seconds if not provided.
           :param actor: Optional actor identifier for namespacing.
           :return: True if the value was set, False if it already exists and nx is True.
        """

        if not self._ocean__redis_client:
            raise RuntimeError("Redis client is not connected")

        ttl = ttl or self._ocean__redis_ttl
        if nx and ttl <= 0:
            raise ValueError(
                "TTL must be greater than 0 when using NX option")

        full_key = f"{self.storage_root}:actors:{actor}:{key}" if actor else f"{self.storage_root}:peer:{key}"

        if isinstance(value, str):
            encoded_value = value.encode("utf-8")
        elif isinstance(value, bytes):
            encoded_value = value
        else:
            encoded_value = json.dumps(value).encode("utf-8")

        existing_value = await self._ocean__redis_client.get(full_key)

        # Idempotency check: skip if same value already present
        if existing_value == encoded_value:
            return None

        await self._ocean__redis_client.set(full_key, encoded_value, ex=ttl, nx=nx)
        self.logger.storage(
            f"Redis SET {full_key}",
            context={"key": full_key, "operation": "set", "ttl": ttl, "nx": nx}
        )
        return [
            {
                "accepted": True,
                "operation": "set",
                "key": full_key,
                "value": value,
                "ttl": ttl,
                "nx": nx
            }
        ]

    async def delete(self, key: str, actor=None) -> Optional[list]:
        if not self._ocean__redis_client:
            raise RuntimeError("Redis client is not connected")

        full_key = f"{self.storage_root}:actors:{actor}:{key}" if actor else f"{self.storage_root}:peer:{key}"

        if not await self.exists(key, actor):
            return None

        await self._ocean__redis_client.delete(full_key)
        self.logger.storage(
            f"Redis DELETE {full_key}",
            context={"key": full_key, "operation": "delete"}
        )
        return [
            {
                "accepted": True,
                "operation": "delete",
                "key": full_key,
                "value": None,
                "ttl": 0,
                "nx": False
            }
        ]

    async def keys(self, pattern: str = "*", actor=None) -> List[str]:
        if not self._ocean__redis_client:
            raise RuntimeError("Redis client is not connected")
        if actor:
            pattern = f"{self.storage_root}:actors:{actor}:{pattern}"
        else:
            pattern = f"{self.storage_root}:peer:{pattern}"
        keys = await self._ocean__redis_client.keys(pattern)
        return [key.decode("utf-8") for key in keys] if keys else []

    async def exists(self, key: str, actor=None) -> bool:
        if not self._ocean__redis_client:
            raise RuntimeError("Redis client is not connected")
        if actor:
            key = f"{self.storage_root}:actors:{actor}:{key}"
        else:
            key = f"{self.storage_root}:peer:{key}"
        return await self._ocean__redis_client.exists(key)

    async def ping(self) -> bool:
        if not self._ocean__redis_client:
            raise RuntimeError("Redis client is not connected")
        return await self._ocean__redis_client.ping()
