import discord
from discord import app_commands, Interaction, Member
from typing import List,TYPE_CHECKING
from discord.ext.commands import Cog
from bot.constants import STATS
from bot.views.views import ConfirmUserDelete

if TYPE_CHECKING:
    from bot.bottekin import Bottekin
    from bot.services.container import ServiceContainer
    from bot.config import Config




class AdminGroup(app_commands.Group, name="admin", description="admin commands", default_permissions=discord.Permissions(administrator=True)):
    def __init__(self,bot: "Bottekin", services:"ServiceContainer", config: "Config"):
        self.bot = bot,
        self.config = config
        self.services = services
        super().__init__()

    
    
    @app_commands.command(name="increment_stats", description="increments or decrements a stat by the given positive or negative number")
    async def increment_stats(self, interaction: Interaction, user: Member, stats:str, count:int) -> None:
        if stats not in STATS:
            await interaction.response.send_message(content="Please select a valid stat name")
            return
        await interaction.response.defer(ephemeral=True)

        await self.services.user.change_stats(user_id=user.id, field=stats, count=count)
        message = (f"User: {user.mention}\n" f"Affected stat: {stats}\n" f"{"Incremented" if count > 0 else "Decremented"} by {count}")
        await interaction.followup.send(message, ephemeral=True)


    @app_commands.command(name="delete_member", description="deletes a user by id")
    async def delete_member(self, interaction: Interaction, user_id:str) -> None:
        try:
            converted_user_id = int(user_id)
        
        except ValueError:
            await interaction.response.send_message("Please enter a valid integer value.", ephemeral=True)
            return

        if interaction.guild is None:
            await interaction.response.send_message("You must call this command inside a guild", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        user = await self.services.user.get_user(user_id=converted_user_id)
        if not user:
            await interaction.followup.send(content="User already does not exist in database", ephemeral=True)
            return
        dc_user = await interaction.guild.fetch_member(converted_user_id)

        if dc_user:
            await interaction.followup.send(content=f"user_id:{user.id}\nusername:{user.display_name}\n**This user is still a member in this server and cannot be removed.**\n")
            return
        
        
        view = ConfirmUserDelete(user=dc_user, admin_id=self.config.admin_id, delete_user_callback=self.services.user.delete_user)
        await interaction.followup.send(view=view, ephemeral=True)
    

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
    

class ModeratorGroup(app_commands.Group, name="moderator", description="moderator commands", default_permissions=discord.Permissions(moderate_members=True)):
    def __init__(self,bot: "Bottekin", services:"ServiceContainer", config: "Config"):
        self.bot = bot,
        self.config = config
        self.services = services
        super().__init__()

    @app_commands.command(name="server_activity", description="Displays server activity data")
    async def server_activity(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        embeds = []
        most_active_dates = await self.services.leaderboard.create_most_active_dates_board()
        server_activity = await self.services.leaderboard.server_activity_board()
        if most_active_dates:
            embeds.append(most_active_dates)
        if server_activity:
            embeds.append(server_activity)

        if not embeds:
            await interaction.followup.send("Not enough data to display.", ephemeral=True)
            return
        await interaction.followup.send(embeds=embeds, ephemeral=True)

class AdminCommandCog(Cog):
    def __init__(self, bot:"Bottekin", services:"ServiceContainer", config:"Config") -> None:
        self.bot = bot
        self.services = services
        self.config = config
        self.admin_group = AdminGroup(bot=bot,services=services,config=self.config)
        self.moderator_group = ModeratorGroup(bot=bot, services=services, config=config)
        super().__init__()
