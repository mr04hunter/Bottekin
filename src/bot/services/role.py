from typing import TYPE_CHECKING
from bot.database.unit_of_work import UnitOfWork
from bot.error_handler.decorators import discord_operation
from bot.logging import get_logger
import discord
from discord import Object
from bot.services.base_service import BaseService
from bot.types.protocols import ChannelProvider

if TYPE_CHECKING:
    from bot.config import Config

logger = get_logger("roles_service")




class RoleService(BaseService):
    def __init__(self, uow: UnitOfWork, bot: ChannelProvider, config:"Config") -> None:
        super().__init__(uow, bot)
        self.config = config

    async def assign_feedback_roles(self) -> None:
        users = await self.uow.users.get_for_feedback_roles()

        if not users:
            logger.info("No users found to assign feedback roles")
            return
        
        for user in users:
            if user.total_feedbacks_given < 15:
                continue
            await self._assign_role_to_member(
                user_id=user.id,
                total=user.total_feedbacks_given,
                role_map=self.config.feedback_roles,
            )

    async def assign_challenge_roles(self) -> None:
        users = await self.uow.users.get_for_challenge_roles()
        if not users:
            logger.warning("No users found for challenge role assignment")
            return

        for user in users:
            await self._assign_role_to_member(
                user_id=user.id,
                total=user.total_submissions,
                role_map=self.config.challenge_roles,
            )

    @discord_operation
    async def _assign_role_to_member(
        self,
        user_id: int,
        total: int,
        role_map: dict,
    ) -> None:
        try:
            member = await self.bot.client.safe_discord_call(coro=self.bot.guild.fetch_member(user_id), operation="assign_role_to_member", default=None)

            if member is None:
                logger.warning("Member could not be fetched, task aborted")
                return
            
            role = self._get_role(total=total, role_map=role_map)
            previous_roles = [
                r for threshold, r in role_map.items()
                if threshold < total and r in member.roles
            ]
            if previous_roles:
                await member.remove_roles(*previous_roles)

            if role and role not in member.roles:
                await member.add_roles(role)

        except discord.NotFound:
            logger.bind(user_id=user_id).warning("Member not found during role assignment")

    def _get_role(self, total: int, role_map: dict) -> Object | None:
        result = None
        for threshold, role in sorted(role_map.items()):
            if total >= threshold:
                result = role
        return result
        