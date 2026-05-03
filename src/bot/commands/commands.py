import discord
from discord import app_commands, Interaction, Client,TextChannel, Message, User
from bot.logging import log_slash_command
from bot.exceptions import BotDatabaseException, BotException, BotNotFoundError, BotValidationError
import traceback as tb
from typing import cast, Sequence, TYPE_CHECKING
from bot.views.views import HelpView, QuoteView
from bot.logging import get_logger
from discord.ext.commands import Cog

if TYPE_CHECKING:
    from bot.bottekin import Bottekin
    from bot.services.container import ServiceContainer
    from bot.scheduler.scheduler import Scheduler
    from bot.make_it_quote.quote_image_gen import QuoteService
    from bot.config import Config

logger = get_logger("commands")




class MainGroup(app_commands.Group, name="bottekin",
                 description="Bot commands"):
    def __init__(self, bot: "Bottekin", services:"ServiceContainer", config:"Config"):
        self.bot = bot
        self.services = services
        self.config = config
        self.stats.add_check(self._is_in_commands_channel)
        super().__init__()


    def _is_in_commands_channel(self,interaction:Interaction) -> bool:
        return interaction.channel_id == self.config.commands_channel_id

    

    @app_commands.command(name="stats", description="display the stats of a user")
    async def stats(self, interaction: Interaction[Client], member: User | None = None) -> None:
        from bot.healthcheck import bot_commands_total
        try:
            await interaction.response.defer(ephemeral=True)
            embeds = []


            target_user = member if member else interaction.user
            is_self = True if target_user == interaction.user else False
            display_name = "You" if is_self else target_user.display_name
            title = f"{target_user.mention} **STATISTICS**"
            try:
                user = await self.services.user.get_with_stats(target_user.id)
            except BotDatabaseException as e:
                raise BotException(
                    message=f"Database error fetching stats for {target_user.id}",
                    user_message="Unable to retrieve stats for the user. Please try again later"
                )
            if not user:
                raise BotNotFoundError(
                    message=f"No stats found for user: {target_user.id}",
                    user_message="No stats found for the user"
                )
            if not interaction.guild:
                raise BotValidationError(
            message="Stats command used outside guild",
            user_message="This command can only be used in a server."
        )
            


            if user and interaction.guild:
                music_embed = await self.services.stats.fetch_music_stats(guild=interaction.guild, user=user, display_name=display_name)
                if music_embed:
                    embeds.append(music_embed)

                feedback_embed = await self.services.stats.fetch_feedback_stats(guild=interaction.guild, user=user, client=interaction.client, display_name=display_name)
                if feedback_embed:
                    embeds.append(feedback_embed)
                    
                challenge_embed = await self.services.stats.fetch_challenge_stats(guild=interaction.guild, user=user, client=interaction.client, display_name=display_name)

                if challenge_embed:
                    embeds.append(challenge_embed)
                

                if not embeds:
                    raise BotNotFoundError(
                        message=f"No embeds generated for {target_user.id}",
                        user_message=f"No stats available for {display_name}."
                    )


                await interaction.followup.send(content=title,embeds=cast(Sequence,embeds), ephemeral=True)
                bot_commands_total.labels(command_name="stats", status="success").inc()

        except app_commands.TransformerError as e:
            raise BotException(message="Transformer Error", user_message="Cannot retrieve the stats of the user, the specified user probably is not a member of this server curently.")
        except Exception as e:
            logger.bind(
                error=str(e),
                traceback=tb.format_exc()
                        ).error("Error on stats command")
            bot_commands_total.labels(command_name="stats", status="error").inc()
            raise



    @app_commands.commands.command(name="help", description="Displays an embed that provides information about the bot & commands")
    @log_slash_command
    async def testtekin_help(self, interaction: discord.Interaction) -> None:
        dev_user = await self.bot.guild.fetch_member(self.config.developer_id)
        rules_channel_url = cast(TextChannel, self.bot.channels.rules)
        help_view = HelpView(dev_user=dev_user, rules_channel_url=rules_channel_url.jump_url)

        await interaction.response.send_message(view=help_view)



class CommandsCog(Cog):
    def __init__(self, bot: "Bottekin", config:"Config", miq_gen:"QuoteService", services:"ServiceContainer", scheduler:"Scheduler") -> None:
        self.bot = bot
        self.services = services
        self.miq_gen = miq_gen
        self.config = config
        self.scheduler = scheduler
        self.main_group = MainGroup(bot=bot, services=services, config=self.config)
        self.miq_command = app_commands.ContextMenu(
            name="make_it_quote",
            callback=self.make_it_quote
        )
        
        self.main_group
        super().__init__()



    
    @log_slash_command
    async def make_it_quote(self, interaction: Interaction, message: Message) -> None:
        try:
            if self.services.miq.is_limited(user_id=interaction.user.id):
                next_available_miq_time = self.scheduler.next_available_miq_time(user_id=interaction.user.id)
                if not next_available_miq_time:
                    await interaction.response.send_message("You cannot make more quotes!")
                    return
                await interaction.response.send_message(f"You cannot make more quotes!\nWait until <t:{int(next_available_miq_time.timestamp())}>")
                return
            
            if len(message.content) > 500:
                await interaction.response.send_message(content="Bruh, this is an essay :x:")
                return

            if len(message.content) < 5:
                await interaction.response.send_message(content="More than 5 character required :x:")
                return


            follow_up_message = await interaction.response.defer(ephemeral=True)

            file_q = await self.miq_gen.create_quote(text=message.content, display_name=message.author.display_name, avatar_url=message.author.display_avatar.url)
            
            view = QuoteView(message=message, file_q=file_q, author_id=message.author.id, caller_id=interaction.user.id)
            await interaction.channel.send(view=view, file=file_q) # type: ignore
            if not follow_up_message:
                return
            await interaction.delete_original_response()
            self.services.miq.increment_usage(user_id=interaction.user.id)
        except Exception as e:
            logger.bind(
                error=str(e) 
            ).error("Error on make_it_quote")
            raise e
