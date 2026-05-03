import discord
from typing import TYPE_CHECKING, Any
from bot.logging import log_function, get_logger

logger = get_logger("converter")

if TYPE_CHECKING:
    from bot.database.models import User
    from bot.types.protocols import ChannelProvider



class BotConverter:
    def __init__(self, bot:"ChannelProvider") -> None:
        self.bot = bot

    @log_function
    async def convert_users_to_members_data(self, data: list[tuple["User",Any]]) -> list[tuple[str,Any]]:
        converted_data = []
        for user_data in data:
            user, val = user_data
            try:
                member = await self.bot.guild.fetch_member(user.id)

                converted_data.append((member.mention,val))
            except discord.NotFound as e:
                logger.bind(
                    user=str(user),
                    val=str(val),
                    error=str(e)
                ).warning("Error fetching member on live_vote_count\nProceeding with the display_name")
                converted_data.append((user.display_name,val)) 
        return converted_data