from datetime import UTC, datetime, timedelta
from discord import Embed
import pytest
from bot.services.sync_services.challenge import ChallengeSync
from unittest.mock import AsyncMock, MagicMock
from tests.factories.discord_factories import make_member, make_message, make_submission_message, make_text_channel, make_reaction, make_thread

class TestChallengeSyncService:
    @pytest.fixture
    async def service(
        self, uow, mock_bot, mock_extractor, mock_challenge_validator,test_config
    ):
        scheduler = MagicMock()
        scheduler.schedule_challenge_jobs = AsyncMock()
        mock_bot.scheduler = scheduler
        mock_bot.channels = MagicMock()
        challenge_sync_service = ChallengeSync(uow=uow, bot=mock_bot, extractor=mock_extractor,
                                 scheduler=AsyncMock(), validator=mock_challenge_validator,
                                 config=test_config)

        return challenge_sync_service
    

    async def test_sync_current_challenge(
            self, service
    ):  
        embed = MagicMock(
            title="test_sync_challenge_title",
            description="test_sync_challenge_description",
            is_active=True,
            is_ongoing_voting=True,
            type="official",
            starts_at=datetime(year=2026, month=3, day=5, tzinfo=UTC),
            ends_at=datetime(year=2026, month=3, day=10, tzinfo=UTC)
        )

        challenge_message = make_message(embeds=[embed], author=MagicMock(id=155149108183695360)) #dyno bot id to simulate

    
        service.bot.channels.challenge_info = make_text_channel(id=111, messages=[challenge_message])

        challenge = await service.sync_current_challenge()

        assert challenge is not None
        assert challenge.id == challenge_message.id
        assert challenge.title == embed.title
        assert challenge.description == embed.description
        assert challenge.starts_at == embed.starts_at
        assert challenge.ends_at == embed.ends_at
        assert challenge.voting_ends_at == embed.ends_at + timedelta(days=1)


    async def test_sync_current_challenge_fetches_the_first_challenge_message(
            self, service
    ):  
        embed = MagicMock(
            title="test_sync_challenge_title",
            description="test_sync_challenge_description",
            is_active=True,
            is_ongoing_voting=True,
            type="official",
            starts_at=datetime(year=2026, month=3, day=5, tzinfo=UTC),
            ends_at=datetime(year=2026, month=3, day=10, tzinfo=UTC)
        )
        
        valid_challenge_message = make_message(
        id=345234232, embeds=[embed],
        author=MagicMock(id=155149108183695360),
        created_at=datetime(year=2026, month=3, day=1, tzinfo=UTC))

        invalid_challenge_message1 = make_message(
        id=345234232, embeds=[embed],
        author=MagicMock(id=23432523),
        created_at=datetime(year=2026, month=3, day=5, tzinfo=UTC))

        invalid_challenge_message2 = make_message(
        id=345784232, embeds=[embed],
        author=MagicMock(id=235), created_at=datetime(year=2026, month=3, day=8, tzinfo=UTC))
    
        messages = [valid_challenge_message, invalid_challenge_message1, invalid_challenge_message2]

        service.bot.channels.challenge_info = make_text_channel(id=111,messages=sorted(messages, key=lambda m: m.created_at))

        challenge = await service.sync_current_challenge()

        assert challenge is not None
        assert challenge.id == valid_challenge_message.id
        assert challenge.title == embed.title
        assert challenge.description == embed.description
        assert challenge.starts_at == embed.starts_at
        assert challenge.ends_at == embed.ends_at
        assert challenge.voting_ends_at == embed.ends_at + timedelta(days=1)


    async def test_sync_current_challenge_skips_invalid_messages(
            self, service
    ):  
        first_challenge_message = make_message(
            id=123456, author=MagicMock(id=155149108183695360),
            created_at=datetime(year=2026, month=3, day=10, tzinfo=UTC))
        
        second_challenge_message = make_message(
            id=123456456, embeds=[MagicMock(spec=Embed)],
            author=MagicMock(id=13233434),
            created_at=datetime(year=2026, month=3, day=5, tzinfo=UTC))
        
        third_challenge_message = make_message(
            id=1234345566456,
            author=MagicMock(id=155149108183695360),
            created_at=datetime(year=2026, month=3, day=8, tzinfo=UTC))
        

        messages = sorted([first_challenge_message,second_challenge_message, third_challenge_message], key=lambda m: m.created_at)


        service.bot.channels.challenge_info = make_text_channel(id=111, messages=messages)

        challenge = await service.sync_current_challenge()

        assert challenge is None
        service.bot.extractor.assert_not_called()

    
        
    async def test_sync_submissions(
            self, service, uow, seeded_challenge
    ):
        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        for message in seeded_challenge.submission_messages:
            assert await uow.challenges.get_submission(message.id) is not None

    async def test_sync_submissions_multiple_paged_channel(
            self, service, uow, seeded_challenge
    ):
        channel = make_text_channel(
        id=service.bot.config.official_submission_channel_id,
        messages=seeded_challenge.submission_messages, page_size=1)

        await service.sync_data(channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        for message in seeded_challenge.submission_messages:
            assert await uow.challenges.get_submission(message.id) is not None

    async def test_sync_duplicate_submissions(
            self, service, uow, seeded_challenge
    ):
        dupl_submission1 = make_submission_message(id=12345, author=seeded_challenge.existing_users.user1)
        dupl_submission2 = make_submission_message(id=123456, author=seeded_challenge.existing_users.user1)

        channel = seeded_challenge.submission_channel

        channel.messages = [*channel.messages,dupl_submission1,dupl_submission2]

        await service.sync_data(channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        author = await uow.users.get_by_id(seeded_challenge.existing_users.user1.id)


        assert author.total_submissions == 1
        assert await uow.challenges.get_submission(dupl_submission1.id) is None
        assert await uow.challenges.get_submission(dupl_submission2.id) is None

    
    async def test_sync_nonexistent_authors_submission_not_inserted(
            self, service, uow, seeded_challenge
    ):
        
        nonexistent_author_id = seeded_challenge.submission_messages[0].author.id
        await uow.users.delete(nonexistent_author_id)
        await service.sync_data(
            seeded_challenge.submission_channel,
            seeded_challenge.challenge,
            [author_id for author_id in seeded_challenge.existing_users.all_ids if author_id!=nonexistent_author_id])


        assert await uow.challenges.get_submission(seeded_challenge.submission_messages[0].id) is None
        

    async def test_sync_submission_after_end_date(
            self, service, uow, seeded_challenge, seeded_users
    ):
        submission = make_submission_message(id=12345, author=MagicMock(id=seeded_users.submission_author1.id), created_at=seeded_challenge.challenge.ends_at+timedelta(days=1))
        seeded_challenge.submission_channel.messages.append(submission)

        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, set(seeded_challenge.existing_users.all_ids+seeded_users.all_ids))

        assert await uow.challenges.get_submission(submission.id) is None
    
    async def test_sync_update_submissions(
            self, service, uow, seeded_challenge
    ):
        
        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        updated_submission_message = seeded_challenge.submission_channel.messages[0]
        updated_submission_message.title = "updated_for_sync_update_submissions"
        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        updated_submission = await uow.challenges.get_submission(seeded_challenge.submission_channel.messages[0].id)

        assert updated_submission.title == "updated_for_sync_update_submissions"



    async def test_sync_submissions_get_cleaned(
            self, service, uow, seeded_challenge
    ):
        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        channel = make_text_channel(messages=[])

        await service.sync_data(channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        for message in seeded_challenge.submission_messages:
            assert await uow.challenges.get_submission(message.id) is None


    async def test_sync_votes(
            self, service, uow, seeded_users, seeded_challenge
    ):

        voter1 = make_member(id=seeded_users.voter1.id)
        voter2 = make_member(id=seeded_users.voter2.id)

        voted_submission = seeded_challenge.submission_messages[0]
        reaction = make_reaction(users=[voter1, voter2])
        voted_submission.reactions = [reaction]

        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, set(seeded_challenge.existing_users.all_ids+seeded_users.all_ids))

        db_voted_submission = await uow.challenges.get_submission(voted_submission.id)

        assert db_voted_submission.total_votes == 2

    async def test_duplicate_votes(
            self, service, uow, seeded_challenge, seeded_users
    ):
        voter1 = make_member(id=seeded_users.voter1.id)

        voted_submission1 = seeded_challenge.submission_messages[0]
        voted_submission2 = seeded_challenge.submission_messages[1]
        reaction1 = make_reaction(users=[voter1])
        reaction2 = make_reaction(users=[voter1])
        voted_submission1.reactions = [reaction1]
        voted_submission2.reactions = [reaction2]

        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, set(seeded_challenge.existing_users.all_ids+seeded_users.all_ids))

        db_voted_submission1 = await uow.challenges.get_submission(voted_submission1.id)
        db_voted_submission2 = await uow.challenges.get_submission(voted_submission2.id)

        assert db_voted_submission1.total_votes == 0
        assert db_voted_submission2.total_votes == 1

    async def test_sync_vote_gets_cleaned(
            self, service, uow, seeded_challenge, seeded_users
    ):
        voter1 = make_member(id=seeded_users.voter1.id)

        voted_submission1 = seeded_challenge.submission_messages[0]
        reaction1 = make_reaction(users=[voter1])
        voted_submission1.reactions = [reaction1]

        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, set(seeded_challenge.existing_users.all_ids+seeded_users.all_ids))

        voted_submission1.reactions = []

        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, set(seeded_challenge.existing_users.all_ids+seeded_users.all_ids))

        db_voted_submission1 = await uow.challenges.get_submission(voted_submission1.id)
        db_voter = await uow.users.get_by_id(voter1.id)
        assert db_voted_submission1.total_votes == 0
        assert db_voter.times_voted == 0

    async def test_sync_vote_after_challenge_ended(
            self, service, uow, seeded_users, seeded_challenge
    ):


        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, set(seeded_challenge.existing_users.all_ids+seeded_users.all_ids))


        voter1 = make_member(id=seeded_users.voter1.id)
        voter2 = make_member(id=seeded_users.voter2.id)

        voted_submission = seeded_challenge.submission_messages[0]
        reaction = make_reaction(users=[voter1, voter2])
        voted_submission.reactions = [reaction]

        challenge = seeded_challenge.challenge

        challenge.is_ongoing_voting = False
        challenge.is_active = False

        await service.sync_data(seeded_challenge.submission_channel, challenge, set(seeded_challenge.existing_users.all_ids+seeded_users.all_ids))

        db_voted_submission = await uow.challenges.get_submission(voted_submission.id)

        assert db_voted_submission.total_votes == 0


    async def test_vote_to_invalid_submission(
            self, service, uow, seeded_challenge, seeded_users
    ):
        invalid_submission = make_submission_message(id=12345, author=MagicMock(id=seeded_challenge.submission_messages[0].author.id))
        voter = make_member(id=seeded_users.voter1.id)

        reaction = make_reaction(users=[voter])
        invalid_submission.reactions = [reaction]

        seeded_challenge.submission_channel.messages.append(invalid_submission)

        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, set(seeded_challenge.existing_users.all_ids+seeded_users.all_ids))

        db_voter = await uow.users.get_by_id(voter.id)

        assert db_voter.times_voted == 0

    async def test_nonexistent_voter_vote_not_inserted(
            self, service, uow, seeded_challenge
    ):
        

        voter1 = make_member(id=123123413)

        voted_submission = seeded_challenge.submission_messages[0]
        reaction = make_reaction(users=[voter1])
        voted_submission.reactions = [reaction]

        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        db_voted_submission = await uow.challenges.get_submission(voted_submission.id)

        assert db_voted_submission.total_votes == 0



    async def test_sync_winners(
            self, service, uow, seeded_challenge, test_config
    ):
        winner_submission = seeded_challenge.submission_messages[0]
        reaction = make_reaction(emoji="🏆", users=[MagicMock(id=test_config.admin_id)])

        winner_submission.reactions = [reaction]

        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        db_winner_submission = await uow.challenges.get_submission(winner_submission.id)

        assert db_winner_submission.winner_declared == True
        assert await uow.challenges.get_winner(winner_submission.author.id, winner_submission.id, seeded_challenge.challenge.id) is not None

    async def test_nonexistent_winner_not_inserted(
            self, service, uow, seeded_challenge, test_config
    ):
        winner_submission = seeded_challenge.submission_messages[0]
        reaction = make_reaction(emoji="🏆", users=[MagicMock(id=test_config.admin_id)])

        winner_submission.reactions = [reaction]

        await service.sync_data(
            seeded_challenge.submission_channel,
            seeded_challenge.challenge,
            [user_id for user_id in seeded_challenge.existing_users.all_ids if user_id!=winner_submission.author.id])

        db_winner_submission = await uow.challenges.get_submission(winner_submission.id)

        assert db_winner_submission is None
        assert await uow.challenges.get_winner(winner_submission.author.id, winner_submission.id, seeded_challenge.challenge.id) is None

    async def test_sync_winner_gets_cleaned(
            self, service, uow, seeded_challenge, test_config
    ):
        winner_submission = seeded_challenge.submission_messages[0]
        reaction = make_reaction(emoji="🏆", users=[MagicMock(id=test_config.admin_id)])

        winner_submission.reactions = [reaction]

        await service.sync_data(
            seeded_challenge.submission_channel,
            seeded_challenge.challenge,
            seeded_challenge.existing_users.all_ids)


        winner_submission.reactions = []

        await service.sync_data(
            seeded_challenge.submission_channel,
            seeded_challenge.challenge,
            seeded_challenge.existing_users.all_ids)


        db_winner_submission = await uow.challenges.get_submission(winner_submission.id)

        assert db_winner_submission.winner_declared == False
        assert await uow.challenges.get_winner(winner_submission.author.id, winner_submission.id, seeded_challenge.challenge.id) is None

    async def test_sync_winner_only_set_by_admin(
            self, service, uow, seeded_challenge
    ):
        winner_submission = seeded_challenge.submission_messages[0]
        reaction = make_reaction(emoji="🏆", users=[MagicMock(id=123312312)])

        winner_submission.reactions = [reaction]

        await service.sync_data(seeded_challenge.submission_channel, seeded_challenge.challenge, seeded_challenge.existing_users.all_ids)

        db_winner_submission = await uow.challenges.get_submission(winner_submission.id)

        assert db_winner_submission.winner_declared == False
        assert await uow.challenges.get_winner(winner_submission.author.id, winner_submission.id, seeded_challenge.challenge.id) is None




    # MONTHLY CHALLENGES #


    async def test_sync_monthly_challenge(self, service, uow, test_config):
        thread1 = make_thread(name = "DAY 1 (02.03.2026) TEST CHALLENGE",id=111111111, owner_id=test_config.admin_id, created_at=datetime(year=2026, month=3, day=2, tzinfo=UTC))
        thread1_starter_message = make_message(
            id=111111111, author=MagicMock(id=test_config.admin_id),
            content="DAY 1 (02.03.2026) TEST CHALLENGE")
        thread1.fetch_message = AsyncMock(return_value=thread1_starter_message)

        thread2 = make_thread(name="DAY 2 (03.03.2026) TEST CHALLENGE",id=1324234234, owner_id=test_config.admin_id, created_at=datetime(year=2026, month=3, day=3, tzinfo=UTC))
        thread2_starter_message = make_message(
            id=1324234234, author=MagicMock(id=test_config.admin_id),
            content="DAY 2 (03.03.2026) TEST CHALLENGE")
        thread2.fetch_message = AsyncMock(return_value=thread2_starter_message)

        thread3 = make_thread(name = "DAY 3 (04.03.2026) TEST CHALLENGE", id=13131345345313, owner_id=test_config.admin_id, created_at=datetime(year=2026, month=3, day=4, tzinfo=UTC))
        thread3_starter_message = make_message(
            id=13131345345313, author=MagicMock(id=test_config.admin_id),
            content="DAY 3 (04.03.2026) TEST CHALLENGE")
        thread3.fetch_message = AsyncMock(return_value=thread3_starter_message)

        thread4 = make_thread(name = "DAY 4 (04.03.2026) TEST CHALLENGE",id=35345345, owner_id=test_config.admin_id, created_at=datetime(year=2026, month=3, day=5))

        thread4_starter_message = make_message(
            id=35345345, author=MagicMock(id=test_config.admin_id, created_at=datetime(year=2026, month=3, day=5, tzinfo=UTC)),
            content="DAY 4 (05.03.2026) TEST CHALLENGE")
        thread4.fetch_message = AsyncMock(return_value=thread4_starter_message)

        thread5 = make_thread(id=345345634, owner_id=test_config.admin_id, created_at=datetime(year=2026, month=3, day=6, tzinfo=UTC))

        thread5_starter_message = make_message(
            id=345345634, author=MagicMock(id=test_config.admin_id),
            content="DAY 5 (06.03.2026) TEST CHALLENGE")
        thread5.fetch_message = AsyncMock(return_value=thread5_starter_message)

        challenge = await service.sync_monthly_challenge([thread1, thread2, thread3, thread4, thread5])

        assert challenge is not None

        assert challenge.title == f"02_03_2026_monthly_challenge"




    
    async def test_sync_monthly_challenge_all(self, service, seeded_monthly_challenge_data):
        service.bot.channels.monthly_challenge_channel = seeded_monthly_challenge_data.submission_channel
        service.bot.guild.active_threads = AsyncMock(return_value=seeded_monthly_challenge_data.submission_channel.threads)
        await service.sync_monthly()

        challenge = await service.uow.challenges.get_current_monthly_challenge()

        assert challenge is not None
        assert challenge.title == seeded_monthly_challenge_data.challenge_title
        assert len(seeded_monthly_challenge_data.submission_messages) != 0 
        assert challenge.total_submissions == len(seeded_monthly_challenge_data.submission_messages)
        assert challenge.starts_at == seeded_monthly_challenge_data.starts_at
        assert challenge.ends_at == seeded_monthly_challenge_data.ends_at
        
        for submission_message in seeded_monthly_challenge_data.submission_messages:
            submission = await service.uow.challenges.get_monthly_submission(submission_message.id)
            assert submission.title == "test_title"
            assert submission.created_at == submission_message.created_at
            assert submission.edited_at == submission_message.edited_at
            assert submission.thread_id == submission_message.channel.id
            assert submission.challenge_id == seeded_monthly_challenge_data.challenge_id



    async def test_sync_monthly_submissions_gets_cleaned(self, service, seeded_monthly_challenge_data, seeded_monthly_challenge, test_config):
        thread_ids = [thread.id for thread in seeded_monthly_challenge_data.threads]

        starter_thread = make_thread(
            id=thread_ids[0], owner_id=test_config.admin_id, name="DAY 1 (01.03.2026) testchallenge", 
            parent_id=seeded_monthly_challenge_data.submission_channel.id,created_at=datetime(year=2026, month=3, day=1, tzinfo=UTC))
        starter_message=make_message(id=starter_thread.id, author=MagicMock(id=test_config.admin_id))
        starter_thread.fetch_message = AsyncMock(return_value=starter_message)
        thread2 = make_thread(
            id=thread_ids[1], owner_id=test_config.admin_id, name="DAY 2 (02.03.2026) testchallenge", 
            parent_id=seeded_monthly_challenge_data.submission_channel.id, created_at=datetime(year=2026, month=3, day=2, tzinfo=UTC))
        thread3 = make_thread(
            id=thread_ids[2], owner_id=test_config.admin_id, name="DAY 3 (02.03.2026) testchallenge", 
            parent_id=seeded_monthly_challenge_data.submission_channel.id, created_at=datetime(year=2026, month=3, day=3, tzinfo=UTC))
        thread4 = make_thread(
            id=thread_ids[3], owner_id=test_config.admin_id, name="DAY 4 (02.03.2026) testchallenge", 
            parent_id=seeded_monthly_challenge_data.submission_channel.id, created_at=datetime(year=2026, month=3, day=4, tzinfo=UTC))
        thread5 = make_thread(
            id=thread_ids[4], owner_id=test_config.admin_id, name="DAY 5 (02.03.2026) testchallenge",
            parent_id=seeded_monthly_challenge_data.submission_channel.id, created_at=datetime(year=2026, month=3, day=5, tzinfo=UTC))

        channel = make_text_channel(id=seeded_monthly_challenge_data.submission_channel.id, archived_threads=[starter_thread, thread2, thread3, thread4])

        service.bot.channels.monthly_challenge_channel = channel
        
        service.bot.guild.active_threads = AsyncMock(return_value=[thread5])

        await service.sync_monthly()

        challenge = await service.uow.challenges.get_current_monthly_challenge()

        assert challenge is not None
        assert challenge.title == seeded_monthly_challenge_data.challenge_title
        assert challenge.total_submissions == 0
        assert challenge.starts_at == starter_thread.created_at
        assert challenge.ends_at == seeded_monthly_challenge_data.ends_at
        

    async def test_sync_monthly_submissions_gets_partial_cleaned(self, service, seeded_monthly_challenge_data, seeded_monthly_challenge, test_config):
        thread_ids = [thread.id for thread in seeded_monthly_challenge_data.threads]


        channel = seeded_monthly_challenge_data.submission_channel

        cleaned_submission_count = len(channel.threads[0].messages)
        submission_count_after_partial_delete = len(seeded_monthly_challenge_data.submission_messages) - cleaned_submission_count


        service.bot.channels.monthly_challenge_channel = channel
        
        service.bot.guild.active_threads = AsyncMock(return_value=[make_thread(
            name="DAY 2 (02.03.2026) testchallenge", id=channel.threads[0].id, owner_id=test_config.admin_id, parent_id=channel.id, created_at=channel.threads[0].created_at)])

        await service.sync_monthly()

        challenge = await service.uow.challenges.get_current_monthly_challenge()
        
        assert challenge is not None
        assert challenge.title == seeded_monthly_challenge_data.challenge_title
        assert challenge.total_submissions != 0
        assert challenge.total_submissions == submission_count_after_partial_delete
        assert challenge.starts_at == seeded_monthly_challenge_data.starts_at
        assert challenge.ends_at == seeded_monthly_challenge_data.ends_at

