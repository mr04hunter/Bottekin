import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.cogs.feedback import FeedbackCog
from tests.factories.discord_factories import make_member, make_message, make_reaction, make_text_channel, make_thread
from discord import ChannelType, DMChannel, RawMessageDeleteEvent, RawMessageUpdateEvent, RawReactionActionEvent

class TestFeedbackCog:
    @pytest.fixture
    async def cog(self, mock_bot, mock_services, test_config, mock_track_extractor):
        return FeedbackCog(bot=mock_bot, services=mock_services, config=test_config, track_extractor=mock_track_extractor)
    


    async def test_unrelated_message_delete(self, cog):
        channel = make_text_channel(id=12312413224234324234) #unrelated channel to feedback channels
        cog.bot.fetch_channel = AsyncMock(return_value=channel)
        payload = MagicMock(spec=RawMessageDeleteEvent)
        payload.channel_id = 12313213
        await cog.on_raw_message_delete(payload=payload)

        cog.services.track.delete_track.assert_not_called()
        cog.services.feedback.delete_feedback.assert_not_called()

    async def test_dm_channel_delete(self, cog):
        channel = MagicMock(spec=DMChannel)
        cog.bot.fetch_channel = AsyncMock(return_value=channel)
        payload = MagicMock(spec=RawMessageDeleteEvent)
        payload.channel_id = 12313213
        await cog.on_raw_message_delete(payload=payload)

        cog.services.track.delete_track.assert_not_called()
        cog.services.feedback.delete_feedback.assert_not_called()

    async def test_feedback_message_delete(self, cog, test_config):
        thread = make_thread(id=8888, type=ChannelType.public_thread, parent_id=test_config.feedback_channel_ids[0], owner_id=12313123)
        cog.bot.fetch_channel = AsyncMock(return_value=thread)
        payload = MagicMock(spec=RawMessageDeleteEvent)
        payload.channel_id = 12313213
        payload.message_id = 12345
        await cog.on_raw_message_delete(payload=payload)
    

        cog.services.track.delete_track.assert_not_called()
        cog.services.feedback.delete_feedback.assert_called_once_with(thread_id=8888, feedback_id=12345)

    async def test_track_message_delete(self, cog, test_config):
        thread = make_thread(id=test_config.feedback_channel_ids[0], type=ChannelType.text, owner_id=12313123)
        cog.bot.fetch_channel = AsyncMock(return_value=thread)
        payload = MagicMock(spec=RawMessageDeleteEvent)
        payload.channel_id = 12313213
        payload.message_id = 12345
        await cog.on_raw_message_delete(payload=payload)
    

        cog.services.track.delete_track.assert_called_once_with(track_id=payload.message_id)
        cog.services.feedback.delete_feedback.assert_not_called()

    
    async def test_message_update_no_content_change(self, cog):
        payload = MagicMock(spec=RawMessageUpdateEvent)
        payload.channel_id = 12313213
        payload.message = make_message(id=12345, content="test_content")
        payload.cached_message = make_message(id=12345, content="test_content")
        await cog.on_raw_message_edit(payload=payload)
    

        cog.services.track.update_track.assert_not_called()
        cog.services.feedback.update_feedback.assert_not_called()

    
    async def test_unreleted_channel_message_update(self, cog, test_config):
        thread = make_thread(id=1324325343, type=ChannelType.text, owner_id=12313123)
        cog.bot.fetch_channel = AsyncMock(return_value=thread)
        payload = MagicMock(spec=RawMessageUpdateEvent)
        payload.channel_id = 12313213
        payload.message = make_message(id=12345, content="test_content")
        payload.cached_message = make_message(id=12345, content="test_content")
        await cog.on_raw_message_edit(payload=payload)
    

        cog.services.track.update_track.assert_not_called()
        cog.services.feedback.update_feedback.assert_not_called()

    async def test_channel_message_with_no_thread_update(self, cog, test_config):
        thread = make_thread(id=test_config.feedback_channel_ids[0], type=ChannelType.text, owner_id=12313123)
        cog.bot.fetch_channel = AsyncMock(return_value=thread)
        payload = MagicMock(spec=RawMessageUpdateEvent)
        payload.channel_id = 12313213
        payload.message = make_message(id=12345, content="test_content")
        payload.cached_message = make_message(id=12345, content="test_content")
        await cog.on_raw_message_edit(payload=payload)
    

        cog.services.track.update_track.assert_not_called()
        cog.services.feedback.update_feedback.assert_not_called()


    async def test_track_message_url_update(self, cog, test_config):
        channel = make_text_channel(id=test_config.feedback_channel_ids[0])
        thread = make_thread(owner_id=1233421, type=ChannelType.public_thread, parent_id=test_config.feedback_channel_ids[0])
        cog.bot.fetch_channel = AsyncMock(return_value=channel)
        payload = MagicMock(spec=RawMessageUpdateEvent)
        payload.channel_id = 12313213
        payload.message_id = 12345
        payload.message = make_message(id=12345, content="http://google.com")
        payload.cached_message = make_message(id=12345, content="http://spotify.com",thread=thread)
        await cog.on_raw_message_edit(payload=payload)
    

        cog.services.track.update_track.assert_called_once_with(track_id=12345, track_data={"title":"test_title", "platform":"test_platform"})
        cog.services.feedback.update_feedback.assert_not_called()

    async def test_track_message_attachment_update(self, cog, test_config):
        channel = make_text_channel(id=test_config.feedback_attachment_channel_ids[0])
        thread = make_thread(owner_id=1233421, type=ChannelType.public_thread, parent_id=test_config.feedback_attachment_channel_ids[0])
        cog.bot.fetch_channel = AsyncMock(return_value=channel)
        payload = MagicMock(spec=RawMessageUpdateEvent)
        payload.channel_id = 12313213
        payload.message_id = 12345
        payload.message = make_message(id=12345, content="no_url", attachments=[MagicMock(title="test_attachment_title_new")])
        payload.cached_message = make_message(id=12345, content="no_url_old",thread=thread, attachments=[MagicMock(title="test_attachment_title")])
        await cog.on_raw_message_edit(payload=payload)
    

        cog.services.track.update_track.assert_called_once_with(track_id=12345, track_data={"title":"test_attachment_title_new", "platform":"attachment"})
        cog.services.feedback.update_feedback.assert_not_called()


    async def test_feedback_message_update(self, cog, test_config):
        thread = make_thread(owner_id=1233421, type=ChannelType.public_thread, parent_id=test_config.feedback_channel_ids[0])
        cog.bot.fetch_channel = AsyncMock(return_value=thread)
        payload = MagicMock(spec=RawMessageUpdateEvent)
        payload.channel_id = 12313213
        payload.message_id = 12345
        payload.message = make_message(id=12345, content="test feedback new")
        payload.cached_message = make_message(id=12345, content="test feedback old",thread=thread)
        await cog.on_raw_message_edit(payload=payload)
    

        cog.services.track.update_track.assert_not_called()
        cog.services.feedback.update_feedback.assert_called_once_with(
            feedback_id=12345, feedback_data={"word_count":3, "content":"test feedback new"})
        
    async def test_reaction_add_bot_returns(self, cog):
        payload = MagicMock(spec=RawReactionActionEvent)
        payload.member = make_member(id=12345, bot=True)
        await cog.on_raw_reaction_add(payload=payload)
    

        cog.services.track.increment_track_reaction.assert_not_called()


    async def test_reaction_author_reacts_own_track(self, cog):
        payload = MagicMock(spec=RawReactionActionEvent)
        payload.member = make_member(id=12345)
        payload.message_author_id = 12345
        await cog.on_raw_reaction_add(payload=payload)
    

        cog.services.track.increment_track_reaction.assert_not_called()


    async def test_add_duplicate_reaction(self, cog):
        payload = MagicMock(spec=RawReactionActionEvent)
        member = make_member(id=12345)
        message = make_message(id=123456)
        reaction1 = make_reaction(users=[member])
        reaction2 = make_reaction(emoji="🖤", users=[member])
        message.reactions = [reaction1, reaction2]

        payload.message_id = 123456
        payload.channel_id = 111
        payload.user_id = 12345
        payload.member = member
        channel = make_text_channel(id=111)
        channel.fetch_message = AsyncMock(return_value=message)
        cog.bot.fetch_channel = AsyncMock(return_value=channel)

        await cog.on_raw_reaction_add(payload=payload)
    

        cog.services.track.increment_track_reaction.assert_not_called()

    async def test_add_reaction(self, cog, test_config):
        payload = MagicMock(spec=RawReactionActionEvent)
        member = make_member(id=12345)
        message = make_message(id=123456)
        reaction1 = make_reaction(emoji="🖤", users=[member])
        message.reactions = [reaction1]

        payload.message_id = 123456
        payload.channel_id = 111
        payload.user_id = 12345
        payload.member = member
        channel = make_text_channel(id=test_config.feedback_channel_ids[0])
        channel.fetch_message = AsyncMock(return_value=message)
        cog.bot.fetch_channel = AsyncMock(return_value=channel)

        await cog.on_raw_reaction_add(payload=payload)
    

        cog.services.track.increment_track_reaction.assert_called_once_with(track_id=123456)

  


    async def test_reaction_remove_bot_returns(self, cog, test_config):
        payload = MagicMock(spec=RawReactionActionEvent)
        payload.member = make_member(id=12345, bot=True)
        payload.user_id = test_config.bot_id
        cog.bot.user = MagicMock(id=test_config.bot_id)
        await cog.on_raw_reaction_remove(payload=payload)
    

        cog.services.track.decrement_track_reaction.assert_not_called()


    async def test_reaction_remove_author_reacts_own_track(self, cog, test_config):
        payload = MagicMock(spec=RawReactionActionEvent)
        message = make_message(id=123456, author=MagicMock(id=12345))
        payload.member = make_member(id=12345)
        payload.user_id = 12345
        channel = make_text_channel(id=test_config.feedback_channel_ids[0])
        channel.fetch_message = AsyncMock(return_value=message)
        cog.bot.fetch_channel = AsyncMock(return_value=channel)
        await cog.on_raw_reaction_remove(payload=payload)
    

        cog.services.track.decrement_track_reaction.assert_not_called()


    
    async def test_remove_reaction(self, cog, test_config):
        payload = MagicMock(spec=RawReactionActionEvent)
        member = make_member(id=12345)
        message = make_message(id=123456, author=MagicMock(id=4353452))
        reaction1 = make_reaction(emoji="🖤", users=[member])
        message.reactions = [reaction1]

        payload.message_id = 123456
        payload.channel_id = 111
        payload.user_id = 12345
        payload.member = member
        channel = make_text_channel(id=test_config.feedback_channel_ids[0])
        channel.fetch_message = AsyncMock(return_value=message)
        cog.bot.fetch_channel = AsyncMock(return_value=channel)
        cog.bot.user = MagicMock(id=test_config.bot_id)
        await cog.on_raw_reaction_remove(payload=payload)
    

        cog.services.track.decrement_track_reaction.assert_called_once_with(track_id=123456)


    
    async def test_on_message_bot_returns(self, cog):
        message = make_message(author=MagicMock(bot=True))

        await cog.on_message(message=message)

        cog.services.track.add_track.assert_not_called()
        cog.services.feedback.add_feedback.assert_not_called()

    async def test_on_message_unrelated_channel_returns(self, cog, test_config):
        track_message = make_message(author=MagicMock(id=123124, bot=False))
        channel = make_text_channel(id=3214324234)
    
        thread = make_thread(owner_id=123124, parent=channel, parent_id=213123123)
        thread.type = ChannelType.public_thread
        feedback_message = make_message(author=MagicMock(id=123123, bot=False))
        feedback_message.channel = thread
        cog.bot.fetch_channel = AsyncMock(return_value=thread)
        channel.fetch_message = AsyncMock(return_value=track_message)
        cog.handle_feedback_track = AsyncMock()
        cog.handle_feedback = AsyncMock()

        await cog.on_message(message=feedback_message)

        cog.handle_feedback.assert_not_called()
        cog.handle_feedback_track.assert_not_called()


    async def test_on_message_handle_track(self, cog, test_config):
        message = make_message(author=MagicMock(id=123124, bot=False))
        channel = make_text_channel(id=test_config.feedback_channel_ids[0])
        message.channel = channel

        cog.handle_feedback_track = AsyncMock()
        cog.handle_feedback = AsyncMock()

        await cog.on_message(message=message)

        cog.handle_feedback.assert_not_called()
        cog.handle_feedback_track.assert_called_once_with(message, message.channel)

    async def test_on_message_handle_feedback(self, cog, test_config):
        track_message = make_message(author=MagicMock(id=123124, bot=False))
        channel = make_text_channel(id=test_config.feedback_channel_ids[0])
    
        thread = make_thread(owner_id=123124, parent=channel, parent_id=test_config.feedback_channel_ids[0])
        thread.type = ChannelType.public_thread
        feedback_message = make_message(author=MagicMock(id=123123, bot=False))
        feedback_message.channel = thread
        cog.bot.fetch_channel = AsyncMock(return_value=thread)
        channel.fetch_message = AsyncMock(return_value=track_message)
        cog.handle_feedback_track = AsyncMock()
        cog.handle_feedback = AsyncMock()

        await cog.on_message(message=feedback_message)

        
        cog.handle_feedback.assert_called_once_with(feedback_message, feedback_message.channel)
        cog.handle_feedback_track.assert_not_called()


    async def test_handle_feedback(self, cog):
        author = make_member(id=1232134, name="test_name", display_name="test_display_name")
        message = make_message(id=213123,content="test_content", author=author)
        thread = make_thread(id=123424, parent_id=3242342, owner_id=123123)

        await cog.handle_feedback(message, thread)

        cog.services.feedback.add_feedback.assert_called()

        kwargs = cog.services.feedback.add_feedback.call_args.kwargs

        data = kwargs["data"]

        assert data.id == 213123
        assert data.track_id == 123424
        assert data.author.id == 1232134
        assert data.author.username == "test_name"
        assert data.author.display_name == "test_display_name"
        assert data.channel_id == 3242342
        assert data.content == "test_content"
        assert data.word_count == 1



    async def test_handle_track_url(self, cog, test_config):
        author = make_member(id=1232134, name="test_name", display_name="test_display_name")
        message = make_message(id=213123,content="http://test.com", author=author)
        channel = make_text_channel(id=test_config.feedback_link_channel_ids[0])

        await cog.handle_feedback_track(message, channel)

        cog.services.track.add_track.assert_called_once_with(
            track_id=message.id, author_id=author.id, thread_id=message.id, channel_id=channel.id, title="test_title", platform="test_platform")


    async def test_handle_track_attachment(self, cog, test_config):
        author = make_member(id=1232134, name="test_name", display_name="test_display_name")
        message = make_message(id=213123,content="attachment", author=author, attachments=[MagicMock(title="test_attachment_title", content_type="audio/mpeg")])
        channel = make_text_channel(id=test_config.feedback_attachment_channel_ids[0])

        await cog.handle_feedback_track(message, channel)

        cog.services.track.add_track.assert_called_once_with(
            track_id=message.id, author_id=author.id, thread_id=message.id, channel_id=channel.id, title="test_attachment_title", platform="attachment")