from discord import RawReactionActionEvent, RawMemberRemoveEvent, Member,Interaction, app_commands, Message
from discord.app_commands import CheckFailure
from datetime import datetime
from typing import TYPE_CHECKING, cast, Callable, Any
import traceback

from bot.logging import log_function
from bot.exceptions import BotException
from bot.logging import get_logger
from bot.views.views import DeleteQuoteButton
from bot.error_handler.decorators import cog_event_handler

if TYPE_CHECKING:
    from bot.bottekin import Bottekin
    from bot.services.container import ServiceContainer
    from bot.config import Config

logger = get_logger("main_events")
def register_events(bot: "Bottekin", services:"ServiceContainer", config:"Config"):


    @bot.event
    async def on_message(message:Message):
        if message.author.bot:
            return
        if message.channel.id == bot.channels.commands_channel.id:
            await bot.client.safe_discord_write_call(
                coro=lambda:message.delete(), operation="commands channel message delete")

    @cog_event_handler
    @bot.event
    async def on_raw_reaction_add(payload: RawReactionActionEvent) -> None:
        if not payload.message_id == config.rules_message_id:
            return
        if not str(payload.emoji) == "✅":
            return
        try:
            if payload.member:
                await services.user.set_purge_data(user_id=payload.user_id, purge=False)
        except Exception as e:
            logger.bind(
                error=str(e),
                user_id=payload.user_id
            ).error("Error while setting privacy option")

    @cog_event_handler
    @bot.event
    async def on_raw_reaction_remove(payload: RawReactionActionEvent) -> None:
        if not payload.message_id == config.rules_message_id:
            return
        if not str(payload.emoji) == "✅":
            return
        try:
            if payload.user_id:
                await services.user.set_purge_data(user_id=payload.user_id, purge=True)
        except Exception as e:
            logger.bind(
                error=str(e),
                user_id=payload.user_id
            ).error("Error while setting privacy option")




    @bot.event
    async def on_error(event: Callable , *args: tuple[Any], **kwargs: dict[Any, Any]) -> None:
        """
        Global event error handler
        """
        logger.bind(
            args=str(args),
            event=event,
            kwargs=str(kwargs),
            traceback=traceback.format_exc()
        ).critical(
            "Unhandled bot error",
        )
    @bot.tree.error
    async def on_app_command_error(interaction: Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, CheckFailure):
            if interaction.response.is_done():
                    await interaction.followup.send(f"Please use {bot.channels.commands_channel.jump_url} for commands", ephemeral=True)
                    return
            else:
                await interaction.response.send_message(f"Please use {bot.channels.commands_channel.jump_url} for commands", ephemeral=True)
                return
        if interaction.command:
            if isinstance(error, app_commands.CommandInvokeError):
                if isinstance(error.original, BotException):
                    if hasattr(error.original, "user_message"):
                        if interaction.response.is_done():
                            await interaction.followup.send(str(error.original.user_message), ephemeral=True)
                        else:
                            await interaction.response.send_message(str(error.original.user_message), ephemeral=True)

                        return
        logger.bind(
            command=interaction.command.name if interaction.command else "unknown",
            user_id=interaction.user.id,
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            error=str(error)
        ).error("App command error")
        if interaction.response.is_done():
            await interaction.followup.send("Unexpected command error, the issue is reported")
        else:
            await interaction.response.send_message("Unexpected command error, the issue is reported")


    @cog_event_handler
    @log_function
    @bot.event
    async def on_member_join(member: Member) -> None:
        reacted_users = {user.id for reaction in bot.channels.rules_message.reactions if str(reaction.emoji) == "✅" async for user in reaction.users()}
        try:
            if not member.bot:
                await services.user.create_user(user_id=member.id, username=str(member), display_name=member.display_name, is_purge_data=not member.id in reacted_users)
                await services.user.clean_user_left_messages(user_id=member.id)
        except Exception as e:
            logger.bind(
                event="on_member_join",
                error=str(e)
            ).error("Error on on_member_join")

    @cog_event_handler
    @log_function
    @bot.event
    async def on_raw_member_remove(payload: RawMemberRemoveEvent) -> None:
        if not payload.user.bot:
            try:
                await services.user.handle_member_leave(user_id=payload.user.id) 
                

            except Exception as e:
                logger.bind(
                    user_id=payload.user.id,
                    function="on_raw_member_remove",
                    error=str(e)
                ).error("Event error")

    @cog_event_handler
    @bot.event
    async def on_ready() -> None:
        await services.leaderboard.create_most_active_dates_board()
        bot.add_dynamic_items(DeleteQuoteButton)
        logger.info(f'{bot.user} has logged in')
        synced = await bot.tree.sync()

        logger.debug(f"SYNCED: {synced}")
        if synced:
            logger.bind(
                synced=str(synced)
            ).debug("SYNCED")
        logger.bind(
            commands=[str(command) for command in bot.commands]
        ).info("COMMANDS")
        await services.leaderboard.cleanup_lb_channel()
        await services.sync_service.sync_all()
        
        if bot and bot.user and bot.guilds:
            logger.info(
                "Discord bot connected",
                bot_id=bot.user.id,
                bot_name=bot.user.name,
                guild_count=len(bot.guilds),
                user_count=sum(cast(int,guild.member_count) for guild in bot.guilds),
                latency=bot.latency,
                timestamp=datetime.utcnow().isoformat()
            )

            
                

            