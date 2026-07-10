"""CancellationToken — cooperative cancellation of long-running runs.

The engine consults the token between ticks. A consumer (API endpoint,
test, CLI) sets the flag; the engine notices it on the next check and
returns early with ``stopped_early=True``.
"""

from __future__ import annotations

from typing import Protocol


class CancellationToken(Protocol):
    """Cooperative cancellation flag."""

    def is_cancelled(self) -> bool: ...

    def cancel(self) -> None: ...
