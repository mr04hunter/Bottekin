
from __future__ import annotations
import discord
from dataclasses import dataclass, field
from discord import TextChannel, Guild
from bot.logging import get_logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.config import Config

logger = get_logger("channel_registry")


@dataclass
class ChannelRegistry:
    leaderboards: TextChannel = field(init=False)
    winners_hall: TextChannel = field(init=False)
    challenge_info: TextChannel = field(init=False)
    rules: TextChannel = field(init=False)
    official_submission: TextChannel = field(init=False)
    commands_channel: TextChannel = field(init=False)
    tiny_submission: TextChannel = field(init=False)
    tracks_no_feedback: TextChannel = field(init=False)
    feedback: list[TextChannel] = field(init=False, default_factory=list)
    rules_message: discord.Message = field(init=False)

    async def populate(self, guild: Guild, config:"Config") -> None:
        self.leaderboards       = await self._fetch(guild, config.leaderboards_channel_id)
        self.winners_hall       = await self._fetch(guild, config.winners_hall_channel_id)
        self.commands_channel = await self._fetch(guild, config.commands_channel_id)
        self.challenge_info     = await self._fetch(guild, config.challenge_info_channel_id)
        self.rules              = await self._fetch(guild, config.rules_channel_id)
        self.official_submission = await self._fetch(guild, config.official_submission_channel_id)
        self.tiny_submission    = await self._fetch(guild, config.tiny_submission_channel_id) 
        self.tracks_no_feedback = await self._fetch(guild, config.tracks_no_feedback_channel_id)
        self.rules_message = await self.rules.fetch_message(config.rules_message_id)
        self.feedback           = [
            await self._fetch(guild, ch_id)
            for ch_id in config.feedback_channel_ids
        ]
        logger.info("Channel registry populated")

    @staticmethod
    async def _fetch(guild: Guild, channel_id: int) -> TextChannel:
        channel = guild.get_channel(channel_id)
        if channel is None:
            logger.bind(channel_id=channel_id).debug(
                "Channel not in cache, fetching from API"
            )
            channel = await guild.fetch_channel(channel_id)
        return channel  # type: ignore[return-value]
    
    