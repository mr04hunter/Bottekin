import pytest
from bot.services.sync_services.track import TrackSyncService
from unittest.mock import AsyncMock, MagicMock
from tests.factories.discord_factories import make_text_channel, make_track_message

class TestTrackSyncService:
    @pytest.fixture
    async def service(
        self, uow, mock_bot, mock_extractor):
        mock_bot.guild = MagicMock()
        mock_bot.guild.fetch_members = AsyncMock()

        return TrackSyncService(uow=uow, bot=mock_bot, extractor=mock_extractor)
    

    async def test_sync_bulk_insert(
            self,service, uow, seeded_members, make_track_messages
    ):
        messages = make_track_messages(authors=seeded_members.all, channel_id=111)
        channel = make_text_channel(
            id=111,
            messages=messages,
            page_size=100
        )
        existing_user_ids = set(seeded_members.all_ids)

        author_track_ids = await service.sync_channel(channel=channel, existing_user_ids=existing_user_ids)

        assert set(author_track_ids.keys()) == {m.id for m in messages}
        assert set(author_track_ids.values()) == {m.author.id for m in messages}

        for message in messages:
            track = await uow.tracks.get(message.id)
            assert track is not None
            assert track.author_id == message.author.id
            assert track.channel_id == message.channel.id

        assert await uow.tracks.get_total_tracks_in_db() == len(messages)



    async def test_sync_bulk_insert_integrit_error_retry(
            self,service, uow, seeded_members, make_track_messages
    ):
        
        message1 = make_track_message(author=seeded_members.user1, channel_id=12345, message_id=7658768567)
        message2 = make_track_message(author=MagicMock(id=123456435546789), channel_id=12345, message_id=765876537768567)
        message3 = make_track_message(author=MagicMock(id=123434556789), channel_id=12345, message_id=76583456368567)
        message4 = make_track_message(author=MagicMock(id=123456734589), channel_id=12345, message_id=7658435546768567)
        message5 = make_track_message(author=MagicMock(id=123456745689), channel_id=12345, message_id=7658768657467567)
        messages = [message1, message2, message3, message4, message5]
        channel = make_text_channel(
            id=111, 
            messages=messages, 
            page_size=100
        )
        existing_user_ids = {*seeded_members.all_ids,123456435546789, 123434556789, 123456734589, 123456745689}

        author_track_ids = await service.sync_channel(channel=channel, existing_user_ids=existing_user_ids)

        assert set(author_track_ids.keys()) == {m.id for m in messages}
        assert set(author_track_ids.values()) == {m.author.id for m in messages}


       

        assert await uow.tracks.get_total_tracks_in_db() == 1

    async def test_sync_cleanup(
            self,service, uow, seeded_members, seeded_track_messages
    ):
 
        channel = make_text_channel(
            id=111,
            messages=[],
            page_size=100
        )
        existing_user_ids = set(seeded_members.all_ids)

        author_track_ids = await service.sync_channel(channel=channel, existing_user_ids=existing_user_ids)

        assert author_track_ids == {}

        for track in seeded_track_messages.all:
            track = await uow.tracks.get(track.id)
            assert track is None

        assert await uow.tracks.get_total_tracks_in_db() == 0

    async def test_sync_partial_cleanup(
            self,service, uow, seeded_members, make_track_messages
    ):
        messages = make_track_messages(authors=seeded_members.all, channel_id=111)
        channel = make_text_channel(
            id=111,
            messages=messages,
            page_size=100
        )
        existing_user_ids = set(seeded_members.all_ids)

        author_track_ids = await service.sync_channel(channel=channel, existing_user_ids=existing_user_ids)

        assert set(author_track_ids.keys()) == {m.id for m in messages}
        assert set(author_track_ids.values()) == {m.author.id for m in messages}

        for message in messages:
            track = await uow.tracks.get(message.id)
            assert track is not None
            assert track.author_id == message.author.id
            assert track.channel_id == message.channel.id

        assert await uow.tracks.get_total_tracks_in_db() == len(messages)


    async def test_duplicate_sync(
            self, service, uow, seeded_members, seeded_track_messages
    ):
        channel = make_text_channel(id=111, messages=seeded_track_messages.all)
        author_track_ids = await service.sync_channel(existing_user_ids=set(seeded_members.all_ids), channel=channel)

        assert set(author_track_ids.keys()) == {m.id for m in seeded_track_messages.all}
        assert set(author_track_ids.values()) == {m.author.id for m in seeded_track_messages.all}

        for message in seeded_track_messages.all:
            track = await uow.tracks.get(message.id)
            assert track is not None
            assert track.author_id == message.author.id
            assert track.channel_id == message.channel.id
            
    
    async def test_nonexistent_author_in_db_tracks_is_not_inserted(
            self, service, uow, seeded_members, seeded_track_messages
    ):
        await uow.users.delete(seeded_members.user1.id)
        existing_user_ids = await uow.users.get_all_ids()
        channel = make_text_channel(id=111, messages=seeded_track_messages.all)

        author_track_ids = await service.sync_channel(existing_user_ids=set(existing_user_ids), channel=channel)

        assert seeded_members.user1.id not in author_track_ids.values()

        tracks_of_nonexisten_user = seeded_track_messages.get_tracks_of_user(seeded_members.user1.id)

        for track in tracks_of_nonexisten_user:
            assert await uow.tracks.get(track.id) is None



    async def test_sync_more_than_one_page(
        self, service, uow, seeded_members, make_track_messages
    ):

        messages = make_track_messages(authors=seeded_members.all, channel_id=111)
        channel = make_text_channel(id=111, messages=messages, page_size=3)
        existing_user_ids = set(seeded_members.all_ids)

        author_track_ids = await service.sync_channel(
            channel=channel, existing_user_ids=existing_user_ids
        )

        assert set(author_track_ids.keys()) == {m.id for m in messages}
        assert await uow.tracks.get_total_tracks_in_db() == len(messages)


    async def test_stale_tracks_removed_across_pages(
    self, service, uow, seeded_members, make_track_messages, make_track
    ):
        messages = make_track_messages(authors=seeded_members.all, channel_id=111)

        stale1 = await make_track(
            id=999999991, author_id=seeded_members.user1.id,
            thread_id=999999991, channel_id=111,
            title="stale1", platform="youtube"
        )
        stale2 = await make_track(
            id=999999992, author_id=seeded_members.user2.id,
            thread_id=999999992, channel_id=111,
            title="stale2", platform="youtube"
        )

        channel = make_text_channel(id=111, messages=messages, page_size=3)
        existing_user_ids = set(seeded_members.all_ids)

        await service.sync_channel(channel=channel, existing_user_ids=existing_user_ids)

        # stale tracks gone
        assert not await uow.tracks.exists(stale1.id)
        assert not await uow.tracks.exists(stale2.id)

        # real tracks survived
        for message in messages:
            assert await uow.tracks.exists(message.id)

    async def test_message_with_no_extractable_title_is_skipped(
    self, service, uow, seeded_members, make_track_messages
    ):
        messages = make_track_messages(authors=seeded_members.all, channel_id=111)
        
        # extractor fails on every message
        service.extractor.extract_track_message_title = AsyncMock(return_value=None)

        channel = make_text_channel(id=111, messages=messages)
        existing_user_ids = set(seeded_members.all_ids)

        author_track_ids = await service.sync_channel(
            channel=channel, existing_user_ids=existing_user_ids
        )

        assert author_track_ids == {}
        assert await uow.tracks.get_total_tracks_in_db() == 0

    async def test_empty_channel_returns_empty(
    self, service, uow, seeded_members
    ):
        channel = make_text_channel(id=111, messages=[])
        existing_user_ids = set(seeded_members.all_ids)

        result = await service.sync_channel(
            channel=channel, existing_user_ids=existing_user_ids
        )

        assert result == {}
        assert await uow.tracks.get_total_tracks_in_db() == 0