# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import os
import json
from typing import Any, Dict, Union, Optional, Callable
from rich.console import Console
from rich.syntax import Syntax
from datetime import datetime

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "application.log")
LOG_QUEUE_KEY = os.getenv("LOG_QUEUE_KEY", "log_queue")
REDACT_KEYS = {
    "private_key", "psk", "token", "secret", "password", "api_key"
}
REDACTED = "**redacted**"
NAUGHTY_WORDS = [
    "bologna", "baloney", "foo", "bar", "baz", "qux",
    "quux", "corge", "grault", "garply", "waldo", "fred", "plugs"
]
console = Console()

LEVELS = {
    "STRACE": 0,
    "TRACE": 1,
    "DEBUG": 2,
    "INFO": 3,
    "WARNING": 4,
    "ERROR": 5,
    "EXCEPTION": 6,
    "TRANSPORT": 7,  # Custom level for transport (TXRX) messages
    "STORAGE": 8,    # Custom level for storage (STOR) messages
    "ECONOMIC": 9    # Custom level for economic/transaction events
}


class Logger:
    def __init__(self):
        self.log_level = LEVELS.get(LOG_LEVEL, None)
        if self.log_level is None:
            raise ValueError(f"Invalid log level: {LOG_LEVEL}")
        self.needsreturn = False
        self.backpressure = 0
        # Optional callback: (level, msg, context)
        self.on_log: Optional[Callable[[str, str, Any], None]] = None

    def redact_and_truncate(self, data: Union[Dict, list, str], max_length: int = 300) -> Any:
        try:
            if isinstance(data, dict):
                return {
                    k: REDACTED if k.lower() in REDACT_KEYS else self.redact_and_truncate(v, max_length)
                    for k, v in data.items()
                }
            elif isinstance(data, list):
                return [self.redact_and_truncate(item, max_length) for item in data]
            elif isinstance(data, str):
                if len(data) > max_length:
                    data = data[:max_length] + "..."
                for word in REDACT_KEYS:
                    if word in data.lower():
                        return REDACTED
                return data
            else:
                return str(data)
        except Exception as e:
            return "[red]<REDACTION ERROR>[/red]"

    async def _enqueue_log(self, level: str, msg: str, context: Any):
        try:
            log_entry = json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": msg,
                "context": context
            })
        except Exception:
            pass

    def log_plain(self, level: str, msg: str, context: Any = None):
        context = context or {}
        redacted_msg = self.redact_and_truncate(msg)
        redacted_ctx = self.redact_and_truncate(context)
        plain_msg = f"[{level}] {redacted_msg}"
        print(plain_msg)
        if redacted_ctx:
            ctx_msg = f"Context: {json.dumps(redacted_ctx, indent=2)}\n"
            print(ctx_msg)

    def log_pretty(self, level: str, msg: str, context: Any = None):
        context = context or {}
        style = "dim" if level in [
            "DEBUG", "TRACE"] else "bold red" if level == "EXCEPTION" else "white"
        redacted_msg = self.redact_and_truncate(msg)
        redacted_ctx = self.redact_and_truncate(context)
        console.print(f"{redacted_msg}", style=style)
        if redacted_ctx:
            console.print(
                Syntax(json.dumps(redacted_ctx, indent=2), "json"), style="dim")

    def _log(self, level: str, msg: str, context: Optional[Dict] = None):
        context = context or {}
        entry_level = LEVELS.get(level.upper())
        if entry_level is None:
            print(f"[WARN] Unknown log level: {level}")
            return

        # Always call the test/debug hook if set
        if self.on_log:
            self.on_log(level, msg, context)

        if entry_level < (self.log_level or 0):
            return

        if self.log_level == 0:
            self.log_plain(level, msg, context)
        else:
            self.log_pretty(level, msg, context)

    def info(self, msg: str, context: Any = None, *args, **kwargs):
        self._log("INFO", msg, context)

    def warning(self, msg: str, context: Any = None, *args, **kwargs):
        self._log("WARNING", msg, context)

    def error(self, msg: str, context: Any = None, *args, **kwargs):
        self._log("ERROR", msg, context)

    def debug(self, msg: str, context: Any = None, *args, **kwargs):
        self._log("DEBUG", msg, context)

    def trace(self, msg: str, context: Any = None, *args, **kwargs):
        self._log("TRACE", msg, context)

    def strace(self, msg: str, context: Any = None, *args, **kwargs):
        self._log("STRACE", msg, context)

    def exception(self, msg: str, context: Any = None, *args, **kwargs):
        self._log("EXCEPTION", msg, context)

    def transport(self, msg: str, context: Any = None, *args, **kwargs):
        """Log a transport (TXRX) event at TRANSPORT level."""
        self._log("TRANSPORT", msg, context)

    def storage(self, msg: str, context: Any = None, *args, **kwargs):
        """Log a storage (STOR) event at STORAGE level."""
        self._log("STORAGE", msg, context)

    def economic(self, msg: str, context: Any = None, *args, **kwargs):
        """Log an economic/transaction event at ECONOMIC level."""
        self._log("ECONOMIC", msg, context)
