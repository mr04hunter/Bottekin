from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import JobExecutionEvent, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from typing import TYPE_CHECKING
from datetime import datetime, UTC, timedelta
from bot.types.common import ChallengeDurationData
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from bot.constants import (challenge_update_data_job_id, 
                        end_challenge_job_id,end_voting_job_id,
                        update_most_active_periods_job_id) 

if TYPE_CHECKING:
    from bot.services.make_it_quote_service import MakeItQuoteService
    from bot.services.leaderboard import LeaderboardService
    from bot.database.unit_of_work import UnitOfWork

from bot.logging import  get_logger

logger = get_logger("scheduler")

class Scheduler(AsyncIOScheduler):
    def __init__(self, uow:"UnitOfWork", gconfig={}, **options):

        super().__init__(gconfig, **options)
        self.miq_rate_limit_job_id_temp = f"miq_rate_limit_"
        self.miq_reset_usage_job_id_temp = f"miq_reset_usage_"
        self.uow = uow

        self.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self.add_listener(self._on_job_missed, EVENT_JOB_MISSED)


    def _on_job_error(self, event: JobExecutionEvent) -> None:
        logger.bind(
            job_id=event.job_id,
            error=str(event.exception),
            traceback=str(event.traceback),
        ).error(f"Scheduled job '{event.job_id}' raised an exception")

    def _on_job_missed(self, event: JobExecutionEvent) -> None:
        logger.bind(
            job_id=event.job_id,
            scheduled_run_time=str(event.scheduled_run_time),
        ).warning(f"Scheduled job '{event.job_id}' missed its execution window")

    def add_reset_miq_usage(self, user_id: int, service: "MakeItQuoteService") -> None:
        if not self.get_job(self.miq_reset_usage_job_id_temp + f"{user_id}"):
            date = datetime.now(tz=UTC) + timedelta(days=1)
            self.add_job(
                service.cleanup_usage, 
                args=[user_id],
                trigger=DateTrigger(date), 
                timezone=UTC, max_instances=1, id=self.miq_reset_usage_job_id_temp+f"{user_id}")

            if not self.running:
                self.start()

    def next_available_miq_time(self, user_id: int) -> datetime | None:
        job = self.get_job(job_id=self.miq_rate_limit_job_id_temp + f"{user_id}")
        if not job:
            return
        return job.next_run_time


    def add_miq_rate_limit_job(self, user_id: int, service:"MakeItQuoteService") -> None:
        if self.get_job(self.miq_reset_usage_job_id_temp + f"{user_id}"):
            self.remove_job(self.miq_reset_usage_job_id_temp + f"{user_id}")
        date = datetime.now(tz=UTC) + timedelta(days=1)
        self.add_job(
                service.remove_limited_user, 
                args=[user_id],
                trigger=DateTrigger(date), 
                timezone=UTC, max_instances=1, id=self.miq_rate_limit_job_id_temp+f"{user_id}")
        
        if not self.running:
            self.start()


    def add_most_active_periods_job(self, service:"LeaderboardService") -> None:
        if self.get_job(job_id=update_most_active_periods_job_id):
            return
        
        self.add_job(
            service.create_most_active_dates_board,
            trigger=IntervalTrigger(hours=24, timezone=UTC),
            coalesce=True, timezone=UTC, max_instances=1,
            id=update_most_active_periods_job_id)
        
        if not self.running:
            self.start()
        

    async def schedule_challenge_jobs(
        self,
        data: ChallengeDurationData
        ) -> None:
        if self.get_job(challenge_update_data_job_id):
            self.remove_job(challenge_update_data_job_id)
        
        if self.get_job(end_challenge_job_id):
            self.remove_job(end_challenge_job_id)

        if self.get_job(end_voting_job_id):
            self.remove_job(end_voting_job_id)


        if not datetime.now(tz=UTC) > data.ends_at:
            self.add_job(
                self.uow.challenges.terminate, 
                trigger=DateTrigger(run_date=data.ends_at), 
                timezone=UTC, max_instances=1, id=end_challenge_job_id)

        
        if not datetime.now(tz=UTC) > data.voting_ends_at:
            self.add_job(
                self.uow.challenges.end_voting, 
                trigger=DateTrigger(run_date=data.voting_ends_at), 
                timezone=UTC, max_instances=1, id=end_voting_job_id)
            

        if not self.running:
            self.start()