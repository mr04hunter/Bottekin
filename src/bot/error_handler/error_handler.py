from __future__ import annotations
from typing import TYPE_CHECKING

from bot.exceptions import (
    BotException, BotDatabaseException, BotDiscordApiError,
    BotRateLimitError, BotExternalApiError, BotSyncError,
    ErrorSeverity, ErrorCode
)
from bot.logging import get_logger

if TYPE_CHECKING:
    from bot.config import Config

logger = get_logger("error_handler")

import asyncio
import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any
from prometheus_client import Counter

from bot.exceptions import (
    BotException, ErrorSeverity, ErrorCode
)
from bot.logging import get_logger

if TYPE_CHECKING:
    from bot.config import Config

logger = get_logger("error_handler")


_error_counter = Counter(
    "bot_errors_total",
    "Total errors by code and severity",
    ["error_code", "severity", "recoverable", "operation"],
)


class ErrorHandler:

    def __init__(self, webhook_url: str | None = None) -> None:
        self._webhook_url = webhook_url

        # error_code → list of timestamps when it occurred
        self._error_timeline: dict[str, list[float]] = defaultdict(list)
        
        # For deduplication: track last alert time per error code
        self._last_alert_time: dict[str, float] = {}

        # Minimum seconds between alerts for the same error code
        self._alert_cooldown = 300.0  # 5 minutes

        # How many errors of the same type trigger an alert
        self._alert_thresholds: dict[ErrorSeverity, int] = {
            ErrorSeverity.CRITICAL: 1,   # Alert on first CRITICAL
            ErrorSeverity.HIGH: 3,        # Alert after 3 HIGH in window
            ErrorSeverity.MEDIUM: 10,     # Alert after 10 MEDIUM in window
            ErrorSeverity.LOW: 0,         # Never alert on LOW
        }


        self._count_window = 600.0  # 10 minutes



    async def observe(
        self,
        exc: BotException,
        operation: str,
    ) -> None:
        error_code = exc.error_code.value if exc.error_code else "UNKNOWN"


        _error_counter.labels(
            error_code=error_code,
            severity=exc.severity.value,
            recoverable=str(exc.recoverable),
            operation=operation,
        ).inc()


        now = time.time()
        self._error_timeline[error_code].append(now)
        self._cleanup_old_entries(error_code, now)

        if self._should_alert(exc, error_code, now):
            self._last_alert_time[error_code] = now
            await self._send_webhook_alert(exc, operation, error_code)

    def get_error_counts(
        self,
        window_seconds: float | None = None,
    ) -> dict[str, int]:

        window = window_seconds or self._count_window
        now = time.time()
        return {
            code: sum(1 for t in timestamps if now - t <= window)
            for code, timestamps in self._error_timeline.items()
        }

    def is_healthy(self) -> tuple[bool, str]:

        counts = self.get_error_counts(window_seconds=60)  

        critical_errors = {
            code: count for code, count in counts.items()
            if count > 0 and any(
                code == e.value for e in [
                    ErrorCode.DB_CONNECTION_FAILED,
                    ErrorCode.DISCORD_CONNECTION_ERROR,
                ]
            )
        }

        if critical_errors:
            worst = max(critical_errors, key=critical_errors.get)  # type: ignore
            return False, f"Critical errors in last 60s: {worst}={critical_errors[worst]}"

        return True, "ok"


    def _cleanup_old_entries(self, error_code: str, now: float) -> None:
        """Remove timestamps outside the count window to prevent memory growth."""
        cutoff = now - self._count_window
        self._error_timeline[error_code] = [
            t for t in self._error_timeline[error_code] if t > cutoff
        ]

    def _should_alert(
        self, exc: BotException, error_code: str, now: float
    ) -> bool:
        if not self._webhook_url:
            return False

        threshold = self._alert_thresholds.get(exc.severity, 0)
        if threshold == 0:
            return False

   
        last_alert = self._last_alert_time.get(error_code, 0)
        if now - last_alert < self._alert_cooldown:
            return False


        recent_count = len(self._error_timeline[error_code])
        return recent_count >= threshold

    async def _send_webhook_alert(
        self,
        exc: BotException,
        operation: str,
        error_code: str,
    ) -> None:
        if not self._webhook_url:
            return

        recent_count = len(self._error_timeline[error_code])
        color = 0xFF0000 if exc.severity == ErrorSeverity.CRITICAL else 0xFF8C00

        embed = {
            "title": f"{'🚨' if exc.severity == ErrorSeverity.CRITICAL else '⚠️'} {exc.severity.value.upper()} — {error_code}",
            "color": color,
            "fields": [
                {
                    "name": "Operation",
                    "value": operation,
                    "inline": True,
                },
                {
                    "name": f"Occurrences (last {int(self._count_window / 60)}min)",
                    "value": str(recent_count),
                    "inline": True,
                },
                {
                    "name": "Recoverable",
                    "value": "Yes" if exc.recoverable else "No",
                    "inline": True,
                },
                {
                    "name": "Message",
                    "value": exc.message[:500],
                    "inline": False,
                },
            ],
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
            ),
        }

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await session.post(
                    self._webhook_url,
                    json={"embeds": [embed]},
                    timeout=aiohttp.ClientTimeout(total=5),
                )
        except Exception as e:
            logger.bind(error=str(e)).warning("Failed to send error webhook alert")