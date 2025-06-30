# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import pytest
import asyncio
from plantangenet.mixins.rox import RoxMixin, WinLoseDraw, a_vs_b, CHOICES


class DummyRox(RoxMixin):
    def __init__(self):
        super().__init__()
        self.events = []

    async def on_rox(self, message: dict):
        self.events.append(("on_rox", message))

    async def on_rox_draw(self, message: dict):
        self.events.append(("draw", message))

    async def on_rox_win(self, message: dict):
        self.events.append(("win", message))

    async def on_rox_loss(self, message: dict):
        self.events.append(("loss", message))


def test_initial_state():
    r = DummyRox()
    assert r.rox_choice in CHOICES
    assert r.rox_winning == WinLoseDraw.UNKNOWN
    assert r.rox_clock_choice == "X"
    assert 0 <= r.rox_index < len(CHOICES)


def test_choose_changes_choice():
    r = DummyRox()
    old_choice = r.rox_choice
    r.choose()
    assert r.rox_choice in CHOICES


def test_status_property_structure():
    r = DummyRox()
    status = r.status
    assert "rox" in status
    rox_status = status["rox"]
    assert isinstance(rox_status, dict)
    assert "choice" in rox_status
    assert "winning" in rox_status
    assert "clock_choice" in rox_status
    assert "index" in rox_status


@pytest.mark.asyncio
async def test_handle_rox_go_valid_choice():
    r = DummyRox()
    msg = {"choice": CHOICES[0]}
    await r.handle_rox_go(msg)
    assert r.rox_choice == msg["choice"]
    assert r.rox_winning == WinLoseDraw.UNKNOWN
    assert ("on_rox", msg) in r.events


@pytest.mark.asyncio
async def test_handle_rox_go_invalid_choice():
    r = DummyRox()
    msg = {"choice": "INVALID"}
    await r.handle_rox_go(msg)
    assert r.rox_winning == WinLoseDraw.ERROR
    assert ("on_rox", msg) in r.events


@pytest.mark.asyncio
async def test_handle_clock_pulse_win(monkeypatch):
    r = DummyRox()
    r._rox__choice = CHOICES[0]
    msg = {"choice": CHOICES[1]}
    monkeypatch.setattr("plantangenet.mixins.rox.a_vs_b",
                        lambda a, b: WinLoseDraw.WIN)
    await r.handle_clock_pulse(msg)
    assert r.rox_winning == WinLoseDraw.WIN
    assert any(event[0] == "win" for event in r.events)


@pytest.mark.asyncio
async def test_handle_clock_pulse_lose(monkeypatch):
    r = DummyRox()
    r._rox__choice = CHOICES[0]
    msg = {"choice": CHOICES[1]}
    monkeypatch.setattr("plantangenet.mixins.rox.a_vs_b",
                        lambda a, b: WinLoseDraw.LOSE)
    await r.handle_clock_pulse(msg)
    assert r.rox_winning == WinLoseDraw.LOSE
    assert any(event[0] == "loss" for event in r.events)


@pytest.mark.asyncio
async def test_handle_clock_pulse_draw(monkeypatch):
    r = DummyRox()
    r._rox__choice = CHOICES[0]
    msg = {"choice": CHOICES[1]}
    monkeypatch.setattr("plantangenet.mixins.rox.a_vs_b",
                        lambda a, b: WinLoseDraw.DRAW)
    await r.handle_clock_pulse(msg)
    assert r.rox_winning == WinLoseDraw.DRAW
    assert any(event[0] == "draw" for event in r.events)


def test_a_vs_b_function():
    assert a_vs_b('🪨', '🪨') == WinLoseDraw.DRAW
    assert a_vs_b('🪨', '✂️') == WinLoseDraw.WIN
    assert a_vs_b('🧻', '🪨') == WinLoseDraw.WIN
    assert a_vs_b('✂️', '🧻') == WinLoseDraw.WIN
    assert a_vs_b('🦎', '🧻') == WinLoseDraw.WIN
    assert a_vs_b('🖖', '✂️') == WinLoseDraw.WIN
