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
            member = await self.bot.client.safe_discord_call(coro=lambda:self.bot.guild.fetch_member(user.id), operation="convert_users_to_members fetch_member")
            if not member:
                logger.bind(
                user=str(user.id),
                val=str(val),
                ).info("Error fetching member on live_vote_count\nProceeding with the display_name")
                converted_data.append((user.display_name,val))
                continue 


            converted_data.append((member.mention,val))

                
        return converted_data