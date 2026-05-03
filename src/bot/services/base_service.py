from bot.database.unit_of_work import UnitOfWork
from bot.logging import get_logger
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider


logger = get_logger("base_service")


class BaseService:
    def __init__(self, uow: UnitOfWork, bot: "ChannelProvider") -> None:
        self.uow = uow
        self.bot = bot

    async def _safe_emit(self, event_name: str, **kwargs) -> None:
        """
        Emit an event without letting a failure in one handler
        crash the originating operation.
        """
        try:
            await self.event_handler.emit_async(event_name, **kwargs)  # type: ignore
        except Exception as e:
            logger.bind(
                event=event_name,
                kwargs=str(kwargs),
                error=str(e),
            ).error(f"Event handler failed for {event_name}, continuing")



    