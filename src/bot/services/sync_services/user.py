from bot.database.unit_of_work import UnitOfWork
from bot.logging import get_logger
from bot.services.base_service import BaseService
from typing import TYPE_CHECKING

from bot.utils.retry import with_retry

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider
logger = get_logger("user_sync_service")

class UserSyncService(BaseService):
    def __init__(self, uow: UnitOfWork, bot: "ChannelProvider") -> None:
        super().__init__(uow, bot)



    async def update_members(self) -> set[int]:
        after = None
        users = []
        user_ids = set()
        reactions = {reaction.emoji:reaction for reaction in self.bot.channels.rules_message.reactions if str(reaction.emoji) == "❌"}
        reaction=reactions.get("❌")
        if reaction:
            reacted_users = await self.bot.client.safe_fetch_reaction_users(reaction=reaction, operation="user_sync purge_data_reactions", default={})
        else:
            reacted_users = []
        if reacted_users:
            reacted_users = {user.id for user in reacted_users if not user.bot}
        logger.bind(
        reacted_users=reacted_users
    ).debug("Reacted users")
        while True:
            members = await self.bot.client.safe_fetch_members(guild=self.bot.guild,limit=100,operation="user_sync_server fetch_members", after=after)
            members = [member for member in members if not member.bot]
            if not members:
                break
            logger.bind(
                users=str(members)
            ).debug("USERS AFTER")
            

            for member in members:
                if member.bot:
                    continue

                users.append({"id":member.id,
                        "username":member.name,
                        "created_at":member.created_at,
                        "display_name":member.display_name,
                        "is_purge_data":member.id in reacted_users})
                user_ids.add(member.id)

                if len(users) >= 100:
                    await self.uow.users.bulk_insert_users(users=users)
                    users.clear()
                
                

            after = members[0].created_at

        if users:
            await self.uow.users.bulk_insert_users(users=users)

        await self.uow.users.cleanup_users(user_ids=user_ids, after=None, before=None)

        return user_ids