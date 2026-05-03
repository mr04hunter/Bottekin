import pytest
from bot.services.role import RoleService
from unittest.mock import AsyncMock, call
from tests.factories.discord_factories import make_member


class TestRoleService:
    @pytest.fixture
    async def service(self, uow, mock_bot, test_config):
        return RoleService(uow=uow, bot=mock_bot,config=test_config)
    

    async def test_assign_feedback_roles(self, service, seeded_feedback_role_users, test_config):
        member = make_member(id=123123)
        service.bot.guild.fetch_member = AsyncMock(return_value=member)

        await service.assign_feedback_roles()

        assert member.add_roles.call_count == 5 

        calls = [
            call(test_config.feedback_roles[1000]),
            call(test_config.feedback_roles[100]),
            call(test_config.feedback_roles[50]),
            call(test_config.feedback_roles[30]),
            call(test_config.feedback_roles[15])
        ]

        member.add_roles.assert_has_calls(calls, any_order=True)

    async def test_assign_feedback_roles_remove_previous_roles(self, service, seeded_feedback_role_users, test_config):
        member = make_member(id=123123, roles=[test_config.feedback_roles[50]])
        service.bot.guild.fetch_member = AsyncMock(return_value=member)

        await service.assign_feedback_roles()

        assert member.add_roles.call_count == 4

        calls = [
            call(test_config.feedback_roles[1000]),
            call(test_config.feedback_roles[100]),
            call(test_config.feedback_roles[30]),
            call(test_config.feedback_roles[15])
        ]

        member.add_roles.assert_has_calls(calls, any_order=True)

        assert member.remove_roles.call_count == 2
        member.remove_roles.assert_called_with(test_config.feedback_roles[50])


    async def test_assign_challenge_roles(self, service, seeded_challenge_role_users, test_config):
        member = make_member(id=123123)
        service.bot.guild.fetch_member = AsyncMock(return_value=member)

        await service.assign_challenge_roles()

        assert member.add_roles.call_count == 5 

        calls = [
            call(test_config.challenge_roles[3]),
            call(test_config.challenge_roles[10]),
            call(test_config.challenge_roles[30]),
            call(test_config.challenge_roles[50]),
            call(test_config.challenge_roles[100])]

        member.add_roles.assert_has_calls(calls, any_order=True)


    async def test_assign_challenge_roles_remove_previous_roles(self, service, seeded_challenge_role_users, test_config):
        member = make_member(id=123123, roles=[test_config.challenge_roles[50]])
        service.bot.guild.fetch_member = AsyncMock(return_value=member)

        await service.assign_challenge_roles()

        assert member.add_roles.call_count == 4

        calls = [
            call(test_config.challenge_roles[3]),
            call(test_config.challenge_roles[10]),
            call(test_config.challenge_roles[30]),
            call(test_config.challenge_roles[100])]

        member.add_roles.assert_has_calls(calls, any_order=True)


        assert member.remove_roles.call_count == 1
        member.remove_roles.assert_called_with(test_config.challenge_roles[50])


    async def test_no_user_to_assign_roles(self, service):
        await service.assign_feedback_roles()
        await service.assign_challenge_roles()

        #no crash: pass


    

