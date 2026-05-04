import discord
from discord import app_commands, Interaction, Member
from typing import List,TYPE_CHECKING
from discord.ext.commands import Cog
from bot.constants import STATS

if TYPE_CHECKING:
    from bot.bottekin import Bottekin
    from bot.services.container import ServiceContainer




class AdminGroup(app_commands.Group, name="admin", description="admin commands", default_permissions=discord.Permissions(administrator=True)):
    def __init__(self,bot: "Bottekin", services):
        self.bot = bot
        self.services = services
        super().__init__()

    
    
    @app_commands.command(name="increment_stats", description="increments or decrements a stat by the given positive or negative number")
    async def increment_stats(self, interaction: Interaction, user: Member, stats:str, count:int) -> None:
        if stats not in STATS:
            await interaction.response.send_message(content="Please select a valid stat name")
            return
        await interaction.response.defer()

        await self.services.user.change_stats(user_id=user.id, field=stats, count=count)
        message = (f"User: {user.mention}\n" f"Affected stat: {stats}\n" f"{"Incremented" if count > 0 else "Decremented"} by {count}")
        await interaction.followup.send(message, ephemeral=True)

    @increment_stats.autocomplete("stats")
    async def change_stats_autocomplete(
        self,
        interaction: Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        
        
        return [
            app_commands.Choice(name=stat, value=stat)
            for stat in STATS if current.lower() in stat.lower()
        ]
    


class AdminCommandCog(Cog):
    def __init__(self, bot:"Bottekin", services:"ServiceContainer") -> None:
        self.bot = bot
        self.services = services
        self.admin_group = AdminGroup(bot=bot,services=services)
        super().__init__()
