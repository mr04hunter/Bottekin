from __future__ import annotations
from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    LOW = "low"          # Expected, no action needed (user input errors)
    MEDIUM = "medium"    # Unexpected but recoverable (API hiccup)
    HIGH = "high"        # Service degraded (repeated failures)
    CRITICAL = "critical" # Service down (DB unreachable, token invalid)


class ErrorCode(Enum):
    DB_CONNECTION_FAILED = "DB_001"
    DB_CONSTRAINT_VIOLATION = "DB_002"
    DB_TIMEOUT = "DB_003"
    DB_UNEXPECTED = "DB_099"

    DISCORD_NOT_FOUND = "DC_001"
    DISCORD_FORBIDDEN = "DC_002"
    DISCORD_RATE_LIMITED = "DC_003"
    DISCORD_HTTP_ERROR = "DC_004"
    DISCORD_CONNECTION_ERROR = "DC_005"

    EXTERNAL_API_TIMEOUT = "EXT_001"
    EXTERNAL_API_RATE_LIMITED = "EXT_002"
    EXTERNAL_API_UNAVAILABLE = "EXT_003"
    EXTERNAL_API_PARSE_ERROR = "EXT_004"

    NOT_FOUND = "BIZ_001"
    VALIDATION_FAILED = "BIZ_002"
    DUPLICATE_ENTRY = "BIZ_003"
    PERMISSION_DENIED = "BIZ_004"
    OPERATION_NOT_ALLOWED = "BIZ_005"

    SYNC_PARTIAL_FAILURE = "SYNC_001"
    SYNC_TOTAL_FAILURE = "SYNC_002"


class BotException(Exception):
    def __init__(
        self,
        message: str,
        user_message: str | None = None,
        error_code: ErrorCode | None = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: dict[str, Any] | None = None,
        recoverable: bool = True,
    ) -> None:
        self.message = message
        self.user_message = user_message
        self.error_code = error_code
        self.severity = severity
        self.context = context or {}
        self.recoverable = recoverable
        super().__init__(self.message)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"code={self.error_code}, "
            f"severity={self.severity}, "
            f"message={self.message!r})"
        )


class BotDatabaseException(BotException):
    def __init__(self, message: str, user_message: str | None = None,
                 error_code: ErrorCode = ErrorCode.DB_UNEXPECTED, **kwargs):
        super().__init__(
            message=message,
            user_message=user_message or "A database error occurred. Please try again.",
            error_code=error_code,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class BotDiscordApiError(BotException):
    def __init__(self, message: str, user_message: str | None = None,
                 error_code: ErrorCode = ErrorCode.DISCORD_HTTP_ERROR,
                 status_code: int | None = None, **kwargs):
        self.status_code = status_code
        super().__init__(
            message=message,
            user_message=user_message or "A Discord API error occurred.",
            error_code=error_code,
            **kwargs
        )


class BotNotFoundError(BotException):
    def __init__(self, message: str, user_message: str | None = None, **kwargs):
        super().__init__(
            message=message,
            user_message=user_message or "The requested resource was not found.",
            error_code=ErrorCode.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            recoverable=False,
            **kwargs
        )


class BotValidationError(BotException):
    def __init__(self, message: str, user_message: str | None = None,
                 field: str | None = None, **kwargs):
        self.field = field
        super().__init__(
            message=message,
            user_message=user_message or "Validation failed.",
            error_code=ErrorCode.VALIDATION_FAILED,
            severity=ErrorSeverity.LOW,
            recoverable=False,
            **kwargs
        )


class BotRateLimitError(BotException):
    def __init__(self, message: str, retry_after: float | None = None,
                 user_message: str | None = None, **kwargs):
        self.retry_after = retry_after
        super().__init__(
            message=message,
            user_message=user_message or "Rate limit reached. Please try again later.",
            error_code=ErrorCode.DISCORD_RATE_LIMITED,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            **kwargs
        )


class BotExternalApiError(BotException):
    def __init__(self, message: str, platform: str | None = None,
                 user_message: str | None = None, **kwargs):
        self.platform = platform
        super().__init__(
            message=message,
            user_message=user_message,
            error_code=ErrorCode.EXTERNAL_API_UNAVAILABLE,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            **kwargs
        )


class BotSyncError(BotException):
    def __init__(self, message: str, partial: bool = True, **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.SYNC_PARTIAL_FAILURE if partial else ErrorCode.SYNC_TOTAL_FAILURE,
            severity=ErrorSeverity.HIGH if not partial else ErrorSeverity.MEDIUM,
            recoverable=partial,
            **kwargs
        )


class LinkTitleExtractorError(BotExternalApiError):
    pass

class PlatformDetectionError(LinkTitleExtractorError):
    pass

class TitleExtractionError(LinkTitleExtractorError):
    pass