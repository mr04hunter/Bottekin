from bot.database.unit_of_work import UnitOfWork
from bot.services.base_service import BaseService
from typing import TYPE_CHECKING
from bot.logging import get_logger
if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider
    from bot.scheduler.scheduler import Scheduler

logger = get_logger("make_it_quote_service")

class MakeItQuoteService(BaseService):

    
    # Rate limit is in memory only, for now. 
    def __init__(
        self,
        uow: UnitOfWork,
        bot: "ChannelProvider",
        scheduler: "Scheduler"
        ) -> None:
        self.miq_user_ids: dict[int,int] = {}
        self.rate_limited_user_ids: list[int] = []
        super().__init__(uow, bot)

        self.scheduler = scheduler

    def is_limited(self, user_id: int) -> bool:
        return user_id in self.rate_limited_user_ids
    
    def increment_usage(self, user_id: int) -> None:
        if user_id not in self.miq_user_ids:
            self.scheduler.add_reset_miq_usage(user_id=user_id, service=self)
            
        current_usage = self.miq_user_ids.get(user_id, 0)
        if current_usage == 4:
            self.miq_user_ids.pop(user_id, None)
            self.rate_limited_user_ids.append(user_id)
            self.scheduler.add_miq_rate_limit_job(user_id=user_id, service=self)
            logger.info(f"{user_id} rate limited")
            return
        self.miq_user_ids[user_id] = current_usage + 1
        logger.info(f"{user_id} use count: {current_usage+1}")
            
    def remove_limited_user(self, user_id: int) -> None:
        logger.info(f"user_id: {user_id} removed rate limit")
        if user_id not in self.rate_limited_user_ids:
            logger.info(f"User {user_id} is not in the rate limited users list")
            return
        self.rate_limited_user_ids.remove(user_id)

    def cleanup_usage(self, user_id: int) -> None:
        logger.info(f"user_id: {user_id} resetted usage")
        self.miq_user_ids.pop(user_id, None) 