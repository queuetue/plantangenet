# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
import asyncio
from collections.abc import Coroutine
import json
import os
from typing import Any, Callable, Optional, Union
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrNoServers
from plantangenet.mixins.transport import TransportMixin
NATS_URLS = os.getenv("NATS_URLS", "nats://localhost:4222").split(",")


class NatsMixin(TransportMixin):
    _ocean_nats__client: Optional[NATS] = None
    _ocean_nats__subscriptions: dict[str, Any] = {}
    _ocean_nats__connected: bool = False
    _ocean_nats__lock: asyncio.Lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._ocean_nats__connected

    @property
    @abstractmethod
    def namespace(self) -> str:
        """Return the namespace of the transport."""

    @property
    @abstractmethod
    def disposition(self) -> str:
        """Return the disposition of the transport."""

    @property
    @abstractmethod
    def logger(self) -> Any:
        """Return the logger instance for this peer."""

    async def update_transport(self):
        if not self._ocean_nats__client:
            self.logger.info(
                f"Transport client not initialized for namespace '{self.namespace}'"
            )
        pass

    async def setup_transport(self, urls) -> None:
        """Setup NATS transport with resilient connection handling."""
        max_retries = 5
        base_delay = 1.0
        max_delay = 30.0
        retry_count = 0

        try:
            while not self._ocean_nats__connected and retry_count < max_retries:
                async with self._ocean_nats__lock:
                    try:
                        if retry_count > 0:
                            self.logger.info(
                                f"Attempting NATS connection (attempt {retry_count + 1}/{max_retries})")
                        self._ocean_nats__client = NATS()
                        await asyncio.wait_for(
                            self._ocean_nats__client.connect(
                                servers=urls,
                                max_reconnect_attempts=3,
                                ping_interval=10,
                                reconnect_time_wait=2,
                                name=f"plantangenet-{self.namespace}",
                                connect_timeout=5  # 5 second timeout
                            ),
                            timeout=10.0  # 10 second overall timeout
                        )
                        await self._ocean_nats__client.publish(
                            f"plantangenet.cluster.{self.namespace}.init",
                            self.disposition.encode()
                        )
                        self._ocean_nats__connected = True
                        if retry_count > 0:
                            self.logger.debug(
                                "NATS connection established successfully")
                        return  # Success, exit the method

                    except (ErrNoServers, OSError, asyncio.TimeoutError) as e:
                        retry_count += 1
                        self._ocean_nats__connected = False
                        if self._ocean_nats__client:
                            try:
                                await self._ocean_nats__client.close()
                            except:
                                pass
                            self._ocean_nats__client = None

                        if retry_count < max_retries:
                            # Exponential backoff with jitter
                            delay = min(
                                base_delay * (2 ** (retry_count - 1)), max_delay)
                            jitter = delay * 0.1 * \
                                (0.5 - asyncio.get_event_loop().time() % 1)
                            total_delay = delay + jitter
                            self.logger.warning(
                                f"NATS connection failed (attempt {retry_count}/{max_retries}): {e}. "
                                f"Retrying in {total_delay:.1f} seconds..."
                            )
                            await asyncio.sleep(total_delay)
                        else:
                            self.logger.error(
                                f"NATS connection failed after {max_retries} attempts: {e}. "
                                "Continuing in offline mode."
                            )

                    except Exception as e:
                        retry_count += 1
                        self._ocean_nats__connected = False
                        if self._ocean_nats__client:
                            try:
                                await self._ocean_nats__client.close()
                            except:
                                pass
                            self._ocean_nats__client = None
                        self.logger.info("Failed to connect to NATS.")

                        if retry_count >= max_retries:
                            self.logger.error(
                                "Maximum NATS connection retries exceeded. Continuing in offline mode.")
                            break

        except asyncio.CancelledError:
            self.logger.warning("NATS setup cancelled")
            if self._ocean_nats__client:
                try:
                    await self._ocean_nats__client.close()
                except:
                    pass
                self._ocean_nats__client = None
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error during NATS setup: {e}")
            self._ocean_nats__connected = False

    async def teardown_transport(self):
        if self._ocean_nats__client:
            await self._ocean_nats__client.close()
            self._ocean_nats__client = None
            self._ocean_nats__connected = False
            self._ocean_nats__subscriptions.clear()

    async def publish(self, topic: str, data: Union[str, bytes, dict]) -> Optional[list]:
        """Publish data to NATS topic with graceful offline handling."""
        if not self._ocean_nats__client or not self._ocean_nats__connected:
            self.logger.debug(f"NATS offline: dropping message to {topic}")
            return  # Fail silently in offline mode

        # Type validation first
        if isinstance(data, dict):
            data = json.dumps(data).encode()
        elif isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            raise TypeError("Data must be bytes, str, or dict")

        try:
            await self._ocean_nats__client.publish(topic, data)
        except (ErrNoServers, OSError, ConnectionError) as e:
            self.logger.warning(f"NATS publish failed for topic {topic}: {e}")
            self._ocean_nats__connected = False  # Mark as disconnected
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error during NATS publish to {topic}: {e}")
            self._ocean_nats__connected = False

    async def subscribe(self, topic: str, callback: Callable[..., Coroutine[Any, Any, Any]]) -> Any:
        """Subscribe to NATS topic with graceful offline handling."""
        if not self._ocean_nats__client or not self._ocean_nats__connected:
            self.logger.warning(f"NATS offline: cannot subscribe to {topic}")
            return None  # Return None instead of raising exception

        try:
            sub = await self._ocean_nats__client.subscribe(
                subject=topic,
                cb=callback
            )
            self._ocean_nats__subscriptions[topic] = sub
            self.logger.debug(f"Successfully subscribed to {topic}")
            return sub
        except (ErrNoServers, OSError, ConnectionError) as e:
            self.logger.warning(
                f"NATS subscribe failed for topic {topic}: {e}")
            self._ocean_nats__connected = False
            return None
        except Exception as e:
            self.logger.exception(
                f"Unexpected error during NATS subscription to {topic}: {e}")
            self._ocean_nats__connected = False
            return None

    async def unsubscribe(self, topic):
        if topic not in self._ocean_nats__subscriptions:
            self.logger.warning(f"No subscription found for topic: {topic}")
            return

        self.logger.error("Unsubscribing is not implemented.")

    async def disconnect(self):
        if self._ocean_nats__client:
            await self._ocean_nats__client.close()
            self._ocean_nats__connected = False
