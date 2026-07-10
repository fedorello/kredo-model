"""Clock — abstraction for current wall-clock time.

The simulation engine itself never reads wall-clock time directly; it
operates in tick units. Clock is for *external* time stamps (when a
run started, when an event was recorded for storage).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Wall-clock time abstraction."""

    def now(self) -> datetime: ...
