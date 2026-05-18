import asyncio
from datetime import datetime, timedelta, UTC
import re
from typing import TYPE_CHECKING, cast

from bot.database.unit_of_work import UnitOfWork
from bot.exceptions import BotDiscordApiError
from bot.logging import get_logger
from discord import NotFound, TextChannel, Embed, Message, File
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
    MOST_ACTIVE_PERIODS_BOARD_TYPE,
    PERIOD_MAP, MONTH_MAP)


from bot.views.embed_builder import EmbedBuilder
from bot.services.base_service import BaseService
from bot.database.models import User

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider
    from bot.utils.converters import BotConverter
    from bot.config import Config
    from bot.services.visualize_data import GraphService

from bot.error_handler.decorators import background_task, discord_operation

logger = get_logger("leaderboard_service")

class LeaderboardService(BaseService):
    def __init__(self, uow: UnitOfWork, bot: "ChannelProvider", converter:"BotConverter", config: "Config", visualize_data:"GraphService") -> None:
        super().__init__(uow, bot)
        self.converter = converter
        self.config = config
        self.visualize = visualize_data


    @discord_operation
    async def create_or_update_leaderboard_message(self, channel: TextChannel, embed: Embed, lb_type: str) -> Message:    
        try:
            lb_message_id = await self.uow.leaderboards.get_lb_message_id(lb_type=lb_type)
            if not lb_message_id:
                lb_message = await self.bot.client.safe_discord_write_call(
                    coro=lambda:channel.send(embed=embed), operation="send_lb_message")
                if not lb_message:
                    raise BotDiscordApiError(message="Failed to send leaderboard message")
                lb_message_id = lb_message.id
                await self.uow.leaderboards.insert_lb_message_id(lb_message_id, lb_type=lb_type)
                return lb_message
            message = await channel.fetch_message(lb_message_id)
            await self.bot.client.safe_discord_write_call(
                coro=lambda:message.edit(embed=embed), operation="lb message update")
            return message 
        except NotFound as e:
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

            await self.bot.client.safe_discord_write_call(
                coro=lambda msg=message:msg.delete(), operation="lb_message delete")
            await asyncio.sleep(0.5)

    @background_task(operation_name="most_active_dates_leaderboard_update")
    async def create_most_active_dates_board(self) -> Embed | None:
        data = await self.uow.leaderboards.get_most_active_periods(admin_id=self.config.admin_id)
        if not data:
            return
        
        periods_data, most_active_member_data = data

        most_active_member = await self.bot.client.safe_discord_call(coro=lambda:self.bot.guild.fetch_member(most_active_member_data.user.id), operation="fetch_most_active_member")
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

        return most_active_periods_embed
        

    @background_task(operation_name="server_activity_board_update")
    async def server_activity_board(self, choice:str) -> File | None:        
        params = PERIOD_MAP[choice.lower()]

        

        activity_data = await self.uow.leaderboards.get_server_activity_data(**params)
        
        if not activity_data:
            return

        if params["trunc_by"] == "month":
            abbreviated = []
            for label in activity_data.labels:
                abbreviated.append(MONTH_MAP[label])

            activity_data.labels = abbreviated

        elif params["trunc_by"] == "day":    
            labels = self.abbreviate_month_names(activity_data.labels)
            if not labels:
                return
            activity_data.labels = labels

        graph_data = self.visualize.create_graph(data=activity_data)
        dc_file = File(fp=graph_data, filename="activity.png")
        return dc_file


    async def get_challenge_role_users(self) -> list[User] | None:
        users = await self.uow.leaderboards.get_challenge_role_users()

        return users
    
    async def get_feedback_role_users(self) -> list[User] | None:
        users = await self.uow.leaderboards.get_feedback_role_users()

        return users
    


    def abbreviate_month_names(self, labels:list) -> list | None:
        
        r = r"([a-zA-Z]*) ([0-9]*)"
        abbreviated_labels = []
        for label in labels:
            groups = re.findall(r, label)

            if not groups:
                return
            
            name, value = groups[0]
            abbreviated_labels.append(f"{MONTH_MAP[name]} {value}")

        return abbreviated_labels