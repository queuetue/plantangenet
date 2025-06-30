# import asyncio
# import pytest

# from plantangenet.gyre.gyre import Gyre
# from plantangenet.drift import Drift
# from plantangenet.mixins.luck import LuckySymbolsMixin
# from plantangenet import GLOBAL_LOGGER
# from dummy_gyre import DummyGyre


# class DummyLuckyDrift(Drift, LuckySymbolsMixin):
#     def __init__(self, gyre, namespace, logger):
#         Drift.__init__(self, gyre=gyre, namespace=namespace, logger=logger)
#         LuckySymbolsMixin.__init__(self)
#         self._on_luck_called = False
#         self._last_message = None

#     async def on_luck(self, message: dict):
#         self._on_luck_called = True
#         self._last_message = message


# @pytest.mark.asyncio
# async def test_gyre_with_lucky_drift():
#     # Step 1: Create Gyre
#     gyre = DummyGyre(
#         drifts=[],
#         logger=GLOBAL_LOGGER,
#         namespace="test-gyre"
#     )

#     # Step 2: Add DummyLuckyDrift
#     drift = DummyLuckyDrift(gyre, namespace="test-drift", logger=GLOBAL_LOGGER)
#     gyre.add_drift(drift)

#     assert drift in gyre.drifts

#     initial_symbols = drift.lucky_symbols

#     # Step 3: Simulate sending a "clock.frame" message
#     msg = {"frame": 42}
#     await drift.handle_lucky_symbols(msg)

#     # Check symbols updated
#     assert len(drift.lucky_symbols) == 9
#     assert drift._on_luck_called
#     assert drift._last_message == msg
#     assert drift.lucky_symbols != initial_symbols


# @pytest.mark.asyncio
# async def test_gyre_with_many_lucky_drifts():
#     # Step 1: Create Gyre
#     gyre = DummyGyre(
#         drifts=[],
#         logger=GLOBAL_LOGGER,
#         namespace="test-gyre"
#     )
#     # Step 2: Add multiple DummyLuckyDrift instances
#     for i in range(5):
#         drift = DummyLuckyDrift(
#             gyre, namespace=f"test-drift-{i}", logger=GLOBAL_LOGGER)
#         gyre.add_drift(drift)

#     assert len(gyre.drifts) == 5


# @pytest.mark.asyncio
# async def test_gyre_with_many_lucky_drifts_diverging():
#     # Create Gyre
#     gyre = DummyGyre(
#         drifts=[],
#         logger=GLOBAL_LOGGER,
#         namespace="test-gyre"
#     )

#     # Add multiple DummyLuckyDrift instances
#     for i in range(85):
#         drift = DummyLuckyDrift(
#             gyre, namespace=f"test-drift-{i}", logger=GLOBAL_LOGGER)
#         gyre.add_drift(drift)

#     assert len(gyre.drifts) == 85

#     # Record initial states
#     initial_symbols = [d.lucky_symbols for d in gyre.drifts]  # type: ignore

#     # Roll forward multiple "frames" to mutate state
#     for frame in range(10):           # Roll 10 frames
#         msg = {"frame": frame}
#         for drift in gyre.drifts:
#             await drift.handle_lucky_symbols(msg)  # type: ignore

#     # Check: All symbols have correct length
#     for drift in gyre.drifts:
#         assert len(drift.lucky_symbols) == 9  # type: ignore

#     # Check: At least one drift changed from its starting state
#     any_changed = any(
#         drift.lucky_symbols != initial  # type: ignore
#         for drift, initial in zip(gyre.drifts, initial_symbols)
#     )
#     assert any_changed, "Expected at least one drift to change symbols"

#     # Optional: Check they are not all identical at the end
#     final_symbols_set = set(
#         d.lucky_symbols for d in gyre.drifts)  # type: ignore
#     assert len(final_symbols_set) > 1, "Expected some divergence between drifts"
