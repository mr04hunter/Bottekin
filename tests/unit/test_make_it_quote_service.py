import pytest
from unittest.mock import MagicMock
from bot.services.make_it_quote_service import MakeItQuoteService

class TestMakeItQuoteService:
    @pytest.fixture
    def service(self, mock_uow,  mock_bot):
        scheduler = MagicMock()
        scheduler.add_miq_rate_limit = MagicMock()
        scheduler.reset_miq_rate_limit = MagicMock()

        return MakeItQuoteService(uow=mock_uow, bot=mock_bot, scheduler=scheduler)
    

    def test_increment_usage(self, service):
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)

        assert service.miq_user_ids[123] == 3


    def test_increment_usage_more_than_five(self, service):
        """ After the use count hits 5, the use cound should reset
            And the user should be rate limited
           """
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)

        assert service.miq_user_ids.get(123) is None
        assert service.is_limited(123) == True

    def test_remove_limited_user(self, service):
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)

        service.remove_limited_user(123)

        assert service.is_limited(123) == False


    def test_remove_limited_nonexistent_user(self, service):
        service.remove_limited_user(123)

        #no crash: pass


    def test_cleanup_usage(self, service):
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)
        service.increment_usage(user_id=123)

        service.cleanup_usage(123)

        assert service.miq_user_ids.get(123) is None

    def test_cleanup_usage_nonexistent_user(self, service):
        service.cleanup_usage(123)

        #no crash: pass