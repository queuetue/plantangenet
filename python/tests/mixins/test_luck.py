import pytest
from plantangenet.mixins.luck import LuckMixin, runs, SYMBOLS


class DummyLucky(LuckMixin):
    def __init__(self):
        super().__init__()
        self.on_luck_called = False
        self.on_luck_message = None

    async def on_luck(self, message: dict):
        self.on_luck_called = True
        self.on_luck_message = message


def test_initial_state():
    dummy = DummyLucky()
    assert isinstance(dummy.lucky_symbols, str)
    assert len(dummy.lucky_symbols) == 9
    assert dummy._lucky_value == 0


def test_lucky_symbols_property():
    dummy = DummyLucky()
    dummy._lucky_symbols = "🦄🦄🦄🦄🦄🦄🦄🦄🦄"
    assert dummy.lucky_symbols == "🦄🦄🦄🦄🦄🦄🦄🦄🦄"


@pytest.mark.asyncio
async def test_handle_lucky_symbols_calls_on_luck():
    dummy = DummyLucky()
    initial_symbols = dummy.lucky_symbols

    msg = {"frame": 42}
    await dummy.handle_lucky_symbols(msg)

    assert len(dummy.lucky_symbols) == 9
    assert dummy.lucky_symbols != initial_symbols
    assert dummy.on_luck_called is True
    assert dummy.on_luck_message == msg


@pytest.mark.asyncio
async def test_lucky_value_calculation_runs(monkeypatch):
    dummy = DummyLucky()

    monkeypatch.setattr(
        "plantangenet.mixins.luck.randint", lambda a, b: 0)
    dummy._lucky_symbols = "🦄🦄🦄🦄🦄🦄🦄🦄🦄"

    before = dummy._lucky_value
    await dummy.handle_lucky_symbols({"test": True})
    after = dummy._lucky_value

    assert after >= before


def test_runs_function():
    assert runs("🦄🦄🦄⭐⭐⭐🌟🌟🌟", 3) == 3
    assert runs("🦄🦄🦄🦄🦄", 5) == 1
    assert runs("🦄⭐🌟🔥💧", 1) == 5
