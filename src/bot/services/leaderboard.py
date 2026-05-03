from datetime import datetime, timedelta, UTC
from typing import TYPE_CHECKING, cast
from bot.database.unit_of_work import UnitOfWork
from bot.logging import get_logger
from discord import TextChannel, Embed, Message
from bot.types.leaderboards.presentation import (
    MostActiveMemberDisplay,
    MostActivePeriodDisplay,
    SubmissionLeaderboardDisplay, 
    AllTimeChallengeLeaderboardDisplay, 
    ChallengeLeaderboardDisplay, FeedbackLeaderboardDisplay,
    ServerActivityDisplay)
from bot.constants import (
    SUBMISSIONS_LEADERBOARD_TYPE,
    FEEDBACK_LEADERBOARD_TYPE,
    CURRENT_CHALLENGE_LEADERBOARD_TYPE,
    ALL_TIME_CHALLENGE_WON_LEADERBOARD_TYPE,
    SERVER_ACTIVITY_LEADERBOARD_TYPE,
    MOST_ACTIVE_PERIODS_BOARD_TYPE)


from bot.views.embed_builder import EmbedBuilder
from bot.services.base_service import BaseService
from bot.database.models import User

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider
    from bot.utils.converters import BotConverter

from bot.error_handler.decorators import background_task, discord_operation

logger = get_logger("leaderboard_service")

class LeaderboardService(BaseService):
    def __init__(self, uow: UnitOfWork, bot: "ChannelProvider", converter:"BotConverter") -> None:
        super().__init__(uow, bot)
        self.converter = converter


    @discord_operation
    async def create_or_update_leaderboard_message(self, channel: TextChannel, embed: Embed, lb_type: str) -> Message:    
        try:
            lb_message_id = await self.uow.leaderboards.get_lb_message_id(lb_type=lb_type)
            if not lb_message_id:
                lb_message = await channel.send(embed=embed)
                lb_message_id = lb_message.id
                await self.uow.leaderboards.insert_lb_message_id(lb_message_id, lb_type=lb_type)
                return lb_message
            message = await channel.fetch_message(lb_message_id)
            await message.edit(embed=embed)
            return message 
        except Exception as e:
            logger.bind(
                error=str(e)
            ).warning("Could not found existing leaderboard message, proceeding to create it")
            message = await channel.send(embed=embed)
            await self.uow.leaderboards.insert_lb_message_id(message.id, lb_type=lb_type)

            return message
        
    @background_task(operation_name="submission_leaderboard_update")
    async def create_or_update_submission_leaderboard(self):
        embed_builder = EmbedBuilder()
        leaderboards_channel = cast(TextChannel, self.bot.channels.leaderboards)
        leaderboard_data = await self.uow.leaderboards.get_submissions_leaderboard()

        lb_member_data = await self.converter.convert_users_to_members_data(data=leaderboard_data.data)
        display_data = SubmissionLeaderboardDisplay(data=lb_member_data, server_total_submissions=leaderboard_data.server_total_submissions,
                                                    server_total_challenges=leaderboard_data.server_total_challenges, 
                                                    leaderboard_length=leaderboard_data.leaderboard_length)
        
        leaderboard_embed = embed_builder.create_all_time_submissions_leaderboards(leaderboard_data=display_data)
        await self.create_or_update_leaderboard_message(channel=leaderboards_channel, embed=leaderboard_embed,
                                                         lb_type=SUBMISSIONS_LEADERBOARD_TYPE)
    @background_task(operation_name="winners_leaderboard_update")
    async def create_or_update_all_time_challenges_won_leaderboard(self):
        embed_builder = EmbedBuilder()
        leaderboards_channel = cast(TextChannel, self.bot.channels.leaderboards)
        leaderboard_data = await self.uow.leaderboards.get_all_time_challenge_leaderboard()
        
        lb_member_data = await self.converter.convert_users_to_members_data(data=leaderboard_data.data)

        display_data = AllTimeChallengeLeaderboardDisplay(data=lb_member_data, server_total_winners=leaderboard_data.server_total_winners,
                                                          leaderboard_length=leaderboard_data.leaderboard_length)

        leaderboard_embed = embed_builder.create_all_time_challenges_won_leaderboards(leaderboard_data=display_data)
        await self.create_or_update_leaderboard_message(channel=leaderboards_channel, embed=leaderboard_embed,
                                                         lb_type=ALL_TIME_CHALLENGE_WON_LEADERBOARD_TYPE)

    @background_task(operation_name="current_challenge_leaderboard_update")
    async def create_or_update_challenge_leaderboard(self) -> None:
        challenge = await self.uow.challenges.get_current()
        if not challenge:
            return
        leaderboard_data = await self.uow.leaderboards.get_challenge_leaderboard(challenge=challenge)
        if not leaderboard_data:
            return
        lb_member_data = await self.converter.convert_users_to_members_data(data=leaderboard_data.data)
        display_data = ChallengeLeaderboardDisplay(data=lb_member_data, challenge_title=leaderboard_data.challenge_title,
                                                   server_total_votes=leaderboard_data.server_total_votes,
                                                   server_total_submissions=leaderboard_data.server_total_submissions)
        embed_builder = EmbedBuilder()

        leaderboard_embed = embed_builder.create_challenge_leaderboard_embed(leaderboard_data=display_data)

        await self.create_or_update_leaderboard_message(channel=cast(TextChannel, self.bot.channels.leaderboards), embed=leaderboard_embed,
                                                         lb_type=CURRENT_CHALLENGE_LEADERBOARD_TYPE)

    @background_task(operation_name="feedback_leaderboard_update")
    async def create_or_update_feedback_leaderboard(self):
        embed_builder = EmbedBuilder()
        leaderboards_channel = cast(TextChannel, self.bot.channels.leaderboards)
        leaderboard_data = await self.uow.leaderboards.get_feedback_leaderboard()

        lb_member_data = await self.converter.convert_users_to_members_data(data=leaderboard_data.data)
        display_data = FeedbackLeaderboardDisplay(data=lb_member_data, server_total_feedback=leaderboard_data.server_total_feedback,
                                                  server_total_fb_words=leaderboard_data.server_total_fb_words,
                                                  server_total_tracks=leaderboard_data.server_total_tracks,
                                                  leaderboard_length=leaderboard_data.leaderboard_length)
        leaderboard_embed = embed_builder.create_feedback_leaderboard(leaderboard_data=display_data)

        await self.create_or_update_leaderboard_message(channel=leaderboards_channel, embed=leaderboard_embed,
                                                            lb_type=FEEDBACK_LEADERBOARD_TYPE)
    
    @discord_operation
    async def cleanup_lb_channel(self) -> None:
        channel = cast(TextChannel, self.bot.channels.leaderboards)
        feedback_lb_message_id = await self.uow.leaderboards.get_lb_message_id(FEEDBACK_LEADERBOARD_TYPE)
        submission_lb_message_id = await self.uow.leaderboards.get_lb_message_id(SUBMISSIONS_LEADERBOARD_TYPE)
        all_time_challenges_message_id = await self.uow.leaderboards.get_lb_message_id(ALL_TIME_CHALLENGE_WON_LEADERBOARD_TYPE)
        current_challenge_lb_message_id = await self.uow.leaderboards.get_lb_message_id(CURRENT_CHALLENGE_LEADERBOARD_TYPE)
        server_activity_lb_message_id = await self.uow.leaderboards.get_lb_message_id(SERVER_ACTIVITY_LEADERBOARD_TYPE)
        most_active_periods_lb_message_id = await self.uow.leaderboards.get_lb_message_id(MOST_ACTIVE_PERIODS_BOARD_TYPE)

        lb_message_ids = [feedback_lb_message_id, submission_lb_message_id,
                         all_time_challenges_message_id, current_challenge_lb_message_id,
                         server_activity_lb_message_id, most_active_periods_lb_message_id]
        
        messages = await self.bot.client.safe_fetch_messages(channel=channel, operation="cleanup_lb_channel", limit=None)
        if not messages:
            return
        for message in messages:
            if message.id in lb_message_ids:
                continue

            await message.delete()

    @background_task(operation_name="most_active_dates_leaderboard_update")
    async def create_most_active_dates_board(self) -> None:
        data = await self.uow.leaderboards.get_most_active_periods()
        if not data:
            return
        
        periods_data, most_active_member_data = data

        most_active_member = await self.bot.client.safe_discord_call(coro=self.bot.guild.fetch_member(most_active_member_data.user.id), operation="fetch_most_active_member")
        most_active_member_name = most_active_member_data.user.display_name
        if most_active_member:
            most_active_member_name = most_active_member.mention

        most_active_member_display_data = MostActiveMemberDisplay(
            member=most_active_member_name, 
            total_feedback=most_active_member_data.total_feedback,
            total_tracks=most_active_member_data.total_tracks)
        
        day = periods_data["day"]
        week = periods_data["week"]
        month = periods_data["month"]

 
        most_active_periods = MostActivePeriodDisplay(
            day=day,
            week=week,
            month=month
        ) 

        embed_builder = EmbedBuilder()

        most_active_periods_embed = embed_builder.create_most_active_periods_board(activity_data=most_active_periods, most_active_member_data=most_active_member_display_data)

        await self.create_or_update_leaderboard_message(channel=self.bot.channels.leaderboards,
                                                        lb_type=MOST_ACTIVE_PERIODS_BOARD_TYPE,embed=most_active_periods_embed)

        logger.debug("createupdated")
        

    @background_task(operation_name="server_activity_board_update")
    async def server_activity_board(self) -> None:
        today_date = datetime.now(tz=UTC) - timedelta(days=1)
        week_date = datetime.now(tz=UTC) - timedelta(weeks=1)
        month_date = datetime.now(tz=UTC) - timedelta(days=30)
        
        async with self.uow.transaction() as t:
            today_activity = await t.leaderboards.get_server_activity_data(date=today_date)
            week_activity = await t.leaderboards.get_server_activity_data(date=week_date)
            month_activity = await t.leaderboards.get_server_activity_data(date=month_date)

            server_activity_display = ServerActivityDisplay(
                today_activity=today_activity,
                week_activity=week_activity,
                month_activity=month_activity
            )

        embed_builder = EmbedBuilder()

        server_activity_embed = embed_builder.create_server_activity_board(activity_data=server_activity_display)

        await self.create_or_update_leaderboard_message(channel=self.bot.channels.leaderboards,
                                                        lb_type=SERVER_ACTIVITY_LEADERBOARD_TYPE,embed=server_activity_embed)


    async def get_challenge_role_users(self) -> list[User] | None:
        users = await self.uow.leaderboards.get_challenge_role_users()

        return users
    
    async def get_feedback_role_users(self) -> list[User] | None:
        users = await self.uow.leaderboards.get_feedback_role_users()

        return users