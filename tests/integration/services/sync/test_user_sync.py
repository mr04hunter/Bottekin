import pytest
from bot.services.sync_services.user import UserSyncService
from unittest.mock import MagicMock
from tests.factories.discord_factories import make_reaction,make_guild

class TestUserSyncService:
    @pytest.fixture
    async def service(self, uow, mock_bot):
        mock_bot.channels.rules_message = MagicMock()
        mock_bot.channels.rules_message.reactions = []
        return UserSyncService(uow=uow, bot=mock_bot)
    
    async def test_user_sync(
            self, service, uow, make_members
    ):
        members = make_members(n=20, seed=10)
        guild = make_guild(members=members)
        service.bot.guild = guild

        user_ids = await service.update_members()

        for user_id in user_ids:
            assert await uow.users.exists(user_id) == True

    async def test_user_sync_multiple_pages(
            self, service, uow, make_members
    ):
        members = make_members(n=20, seed=10)
        guild = make_guild(members=members, page_size=1)
        service.bot.guild = guild

        user_ids = await service.update_members()

        for user_id in user_ids:
            assert await uow.users.exists(user_id) == True

    async def test_stale_users_in_db_are_cleaned(
            self, service, seeded_members, uow, make_members
    ):
        members = make_members(n=20, seed=10)
        guild = make_guild(members=members)
        service.bot.guild = guild

        user_ids = await service.update_members()

        for user_id in user_ids:
            assert await uow.users.exists(user_id) == True

        for user_id in seeded_members.all_ids:
            assert await uow.users.exists(user_id) == False


    async def test_is_purge_data_updates_correctly(
            self, service, seeded_members, uow
    ):

        guild = make_guild(members=seeded_members.all)
        service.bot.guild = guild
        reactions = make_reaction(emoji="✅", users=[seeded_members.user1, seeded_members.user2])

        service.bot.channels.rules_message.reactions = [reactions]

        await service.update_members()

        user1 = await uow.users.get_by_id(seeded_members.user1.id)
        assert user1.is_purge_data == False

        user2 = await uow.users.get_by_id(seeded_members.user2.id)
        assert user2.is_purge_data == False

    async def test_fields_update_correctly(
            self, service, uow, seeded_members
    ):
        reactions = make_reaction(emoji="✅", users=seeded_members.all)

        service.bot.channels.rules_message.reactions = [reactions]

        seeded_members.user1.name = "test_sync_updated_username1"
        seeded_members.user1.display_name = "test_sync_updated_display_name1"

        seeded_members.user2.name = "test_sync_updated_username2"
        seeded_members.user2.display_name = "test_sync_updated_display_name2"

        guild = make_guild(members=seeded_members.all)
        service.bot.guild = guild

        await service.update_members()

        user1 = await uow.users.get_by_id(seeded_members.user1.id)
        assert user1.username == "test_sync_updated_username1"
        assert user1.display_name == "test_sync_updated_display_name1"

        user2 = await uow.users.get_by_id(seeded_members.user2.id)
        assert user2.username == "test_sync_updated_username2"
        assert user2.display_name == "test_sync_updated_display_name2"