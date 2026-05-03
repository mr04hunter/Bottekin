import discord
from discord.ext import commands
from discord import Member
from bot.logging import log_function, get_logger
from bot.registry.channel_registry import ChannelRegistry

from typing import TYPE_CHECKING
from bot.integrations.discord.client import DcClient
if TYPE_CHECKING:
    from bot.config import Config



logger = get_logger("bot")

class Bottekin(commands.Bot):
    def __init__(
        self,
        config:"Config",
        channels:"ChannelRegistry") -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='/', intents=intents)
        self.client = DcClient(bot=self)
        self.config = config
        self.channels = channels
        

    @log_function
    async def get_member_named(self, name: str) -> Member | None:
        guild = self.get_guild(self.config.guild_id)
        if not guild:
            guild = await self.fetch_guild(self.config.guild_id)
        
        return guild.get_member_named(name)


    async def setup_hook(self) -> None:

        self.guild = await self.fetch_guild(int(self.config.guild_id))
        if self.guild is None:
            return
        await self.channels.populate(guild=self.guild, config=self.config)   

     


def create_bot(channels:"ChannelRegistry", config:"Config") -> Bottekin:
    return Bottekin(channels=channels, config=config)