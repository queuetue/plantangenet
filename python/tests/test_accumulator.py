# tests/plantangenet/lib/clock/test_accumulator.py
import pytest
from plantangenet.services.clock.accumulator import Accumulator


def test_initialization_defaults():
    acc = Accumulator(cycle_length=60)
    d = acc.to_dict()
    assert d["cycle_length"] == 60
    assert d["running"] is True
    assert d["repeating"] is False
    assert d["accumulator"] == 0.0
    assert d["cycles"] == 0


def test_accumulate_non_repeating_partial_frame():
    acc = Accumulator(cycle_length=10, repeating=False)
    acc.accumulate(0.05)  # less than 1/10th of a second
    assert 0 < acc.to_dict()["accumulator"] < 0.1
    assert acc.to_dict()["cycles"] == 0


def test_accumulate_non_repeating_full_frame():
    acc = Accumulator(cycle_length=10, repeating=False)
    acc.accumulate(0.1)  # exactly 1 frame
    assert acc.to_dict()["accumulator"] == 0.0
    assert acc.to_dict()["cycles"] == 0


def test_accumulate_repeating_multiple_frames():
    acc = Accumulator(cycle_length=2, repeating=True)  # frame_duration = 0.5
    acc.accumulate(1.2)  # should yield 2 full cycles, 0.2 leftover
    d = acc.to_dict()
    assert d["cycles"] == 2
    assert pytest.approx(d["accumulator"], 0.01) == 0.2


def test_accumulate_when_not_running():
    acc = Accumulator(cycle_length=10, running=False)
    acc.accumulate(0.5)
    d = acc.to_dict()
    assert d["accumulator"] == 0.0
    assert d["cycles"] == 0


def test_reset():
    acc = Accumulator(cycle_length=30, repeating=True)
    acc.accumulate(1.0)
    acc.reset()
    d = acc.to_dict()
    assert d["accumulator"] == 0.0
    assert d["cycles"] == 0


def test_to_dict_structure():
    acc = Accumulator(cycle_length=20, running=False, repeating=True)
    d = acc.to_dict()
    assert set(d.keys()) == {"cycle_length", "running",
                             "repeating", "accumulator", "cycles"}
    assert d["running"] is False
    assert d["repeating"] is True
