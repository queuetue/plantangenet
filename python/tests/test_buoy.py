# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Tests for Buoy - time-aware Shard with clock synchronization.

Tests cover:
- Buoy initialization and time management
- Clock pulse handling and synchronization
- Leader and heartbeat message handling
- Luck calculation and symbol management
- Frame and pulse processing
"""

import pytest
from plantangenet import GLOBAL_LOGGER
from models.fake_buoy import FakeBuoy


@pytest.fixture
def buoy(mock_logger):
    """Create a Buoy instance for testing."""
    return FakeBuoy(logger=GLOBAL_LOGGER, namespace="test-namespace")


class TestBuoyInitialization:
    """Test Buoy initialization and basic properties."""

    def test_default_initialization(self):
        """Test Buoy with default parameters."""
        buoy = FakeBuoy(
            logger=GLOBAL_LOGGER,
            namespace="test"
        )

        assert buoy.ocean_ready is True
        assert buoy._ocean__logger == GLOBAL_LOGGER
        assert buoy.namespace == "test"
        assert buoy._ocean__id is not None
        assert buoy.storage_root == f"root:test:{buoy._ocean__id}:storage"
        assert buoy._ocean__nickname is not None
        assert buoy._ocean__clock_frame == 0
        assert buoy._ocean__disposition is not None
        assert buoy._ocean__frame_delta == 0
        assert not buoy._ocean__timebase_paused
        assert not buoy._ocean__timebase_stepping

    def test_custom_redis_prefix(self):
        """Test Buoy with custom redis prefix."""
        b = FakeBuoy(
            logger=GLOBAL_LOGGER,
            namespace="test",
            redis_prefix="custom"
        )
        match_text = f"custom:test:{b._ocean__id}:storage"
        assert b.storage_root == match_text

    def test_health_field_registration(self):
        b = FakeBuoy(
            logger=GLOBAL_LOGGER,
            namespace="test",
            redis_prefix="custom"
        )
        assert "health" in b._status_tracked_fields  # type: ignore
        meta = b._status_tracked_fields["health"].meta  # type: ignore

    def test_health_default_value(self):
        b = FakeBuoy(logger=GLOBAL_LOGGER, namespace="test")
        assert b.health == 100

    def test_health_set_and_dirty(self):
        b = FakeBuoy(logger=GLOBAL_LOGGER, namespace="test")
        b.health = 75
        assert b.health == 75
        assert b.dirty
        assert "health" in b.dirty_fields
        assert b.dirty_fields["health"] is True
        assert "health" in b.dirty_fields_list

    def test_health_clear_dirty(self):
        b = FakeBuoy(logger=GLOBAL_LOGGER, namespace="test")
        b.health = 42
        b.clear_dirty()
        assert not b.dirty

    def test_status_property_includes_health(self):
        b = FakeBuoy(logger=GLOBAL_LOGGER, namespace="test")
        b.health = 55
        s = b.status
        assert "health" in s["fakebuoy"]
        assert s["fakebuoy"]["health"]["value"] == 55
        assert s["fakebuoy"]["health"]["dirty"] is True

    def test_to_dict_includes_health(self):
        b = FakeBuoy(logger=GLOBAL_LOGGER, namespace="test")
        b.health = 99
        d = b.to_dict()
        assert d["health"] == 99
