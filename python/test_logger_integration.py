# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

import pytest
from plantangenet.logger import Logger


class Dummy:
    """Dummy class to test logger mixin usage."""

    def __init__(self, logger=None):
        self._logger = logger or Logger()

    @property
    def logger(self):
        return self._logger


def test_logger_economic_hook():
    logs = []
    logger = Logger()
    logger.on_log = lambda level, msg, ctx: logs.append((level, msg, ctx))
    dummy = Dummy(logger)
    dummy.logger.economic("economic event", context={"foo": 1})
    assert any(l[0] == "ECONOMIC" and l[1] == "economic event" for l in logs)


def test_logger_transport_hook():
    logs = []
    logger = Logger()
    logger.on_log = lambda level, msg, ctx: logs.append((level, msg, ctx))
    dummy = Dummy(logger)
    dummy.logger.transport("txrx event", context={"bar": 2})
    assert any(l[0] == "TRANSPORT" and l[1] == "txrx event" for l in logs)


def test_logger_storage_hook():
    logs = []
    logger = Logger()
    logger.on_log = lambda level, msg, ctx: logs.append((level, msg, ctx))
    dummy = Dummy(logger)
    dummy.logger.storage("stor event", context={"baz": 3})
    assert any(l[0] == "STORAGE" and l[1] == "stor event" for l in logs)


def test_logger_debug_hook_prints(capsys):
    logger = Logger()
    logger.on_log = lambda level, msg, ctx: print(f"HOOK: {level} {msg} {ctx}")
    logger.economic("test econ", context={"x": 42})
    out = capsys.readouterr().out
    assert "HOOK: ECONOMIC test econ" in out
