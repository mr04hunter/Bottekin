from unittest.mock import AsyncMock, MagicMock
from discord import Embed
import pytest
from bot.types.common import MonthlyChallengeData, UserData
from bot.types.tests.challenge import ChallengeSyncData, MonthlyChallengeSyncData
from tests.factories.discord_factories import (
    make_feedback_message, make_member,
    make_message,
    make_text_channel, make_track_message, 
    make_thread, make_submission_message)
from bot.types.tests.user import MemberCollection
from bot.types.tests.track import TrackMessageCollection, ThreadCollection
from bot.types.tests.feedback import  FeedbackMessageCollection
import random
from datetime import datetime, UTC, timedelta
from bot.types.common import ChallengeDurationData, ChallengeEmbedData


@pytest.fixture
def make_members():
    def _make(
            n:int = 10,
            seed:int | None = None
    ) -> list[MagicMock]:
        if seed is not None:
            random.seed(seed)

        ids = random.sample(range(100_000_000, 999_999_999), n)
        return [make_member(uid) for uid in ids]
    
    return _make





def make_valid_feedback_content() -> str:


    with open("words.txt") as f: # type: ignore
        WORD_LIST = [w.strip().lower() for w in f]

        return "".join([word+" " for word in random.choices(WORD_LIST, k=15)])

def make_invalid_feedback_content() -> str:
    invalid_words = ["asdfsdf", "sdfsdfsdf", "fdsfkşlasdfgkşlg", "sdfkdgs", "sdgfsdfgd"]
    return "".join(random.choices(invalid_words, k=random.randint(1,30)))



# @pytest.fixture
# def challenge_service(uow, mock_bot, mock_extractor, test_config):
#     service = ChallengeService(uow=uow, bot=mock_bot,extractor=mock_extractor,event_handler=AsyncMock(), scheduler=AsyncMock())
#     # get_submission_data touches the extractor (HTTP) so mock that path
#     async def real_get_submission_data(message, challenge):
#         title = mock_bot.extractor.get_submission_title(message=message)
#         return {
#             "id": message.id,
#             "author_id": message.author.id,
#             "channel_id": message.channel.id,
#             "title": title,
#             "challenge_id": challenge.id,
#             "created_at": message.created_at,
#             "edited_at": message.edited_at
#         }
    
#     def validate(message, challenge):
#         if challenge.type == "community" and message.channel.id == test_config.official_submission_channel_id:
#             return False
    
#         if challenge.type == "official" and message.channel.id == test_config.tiny_submission_channel_id:
#             return False
        
#         if message.channel.id not in test_config.submission_channel_ids:
#             return False
        
#         if message.created_at > challenge.ends_at:
#             return False
        
#         return True


#     service.get_submission_data = real_get_submission_data #type: ignore
#     return service





# @pytest.fixture
# def mock_bot(mock_bot, challenge_service):  # extends the base fixture
#     mock_bot.services = MagicMock()
#     mock_bot.services.challenge = challenge_service
#     mock_bot.services.sync_service = MagicMock()
#     mock_bot.services.sync_service.sync_track_with_no_feedback = AsyncMock()
#     return mock_bot


@pytest.fixture
def make_feedback_messages():
    def _make(
        authors: list[MagicMock],
        tracks:list[MagicMock],
        n:int | None = None,
        all_valid:bool = True
    ):

        if n is None:
            n = len(authors)
        

        
        valid_pairs = [
            (member, track)
            for member in authors
            for track in tracks
            if track.author.id != member.id
        ]

        random.shuffle(valid_pairs)

        used_ids = set()
        messages = []
        used_pairs = set()

        for member, track in valid_pairs[:n]:
            if (member.id, track.id) in used_pairs:
                continue
            message_id = random.randint(100_000_000, 999_999_999)
            while message_id in used_ids:
                message_id = random.randint(100_000_000, 999_999_999)

            used_ids.add(message_id)
            content = make_valid_feedback_content() if all_valid else make_invalid_feedback_content()

            
            used_pairs.add((member.id, track.id))
            messages.append(make_feedback_message(content,member, track.id, track.channel.id, message_id))

        return sorted(messages, key=lambda message: message.id)
    return _make


@pytest.fixture
def make_track_messages():
    def _make(
            authors: list[MagicMock],
            channel_id:int,
            n:int | None = None,
    ):
        if n is None:
            n = len(authors)

        chosen = random.choices(authors, k=n)
        used_ids = set()
        messages = []

        for member in chosen:
            message_id = random.randint(100_000_000, 999_999_999)
            while message_id in used_ids:
                message_id = random.randint(100_000_000, 999_999_999)
            
            used_ids.add(message_id)
            messages.append(make_track_message(member, channel_id, message_id))
        
        return sorted(messages, key=lambda message: message.id)
    
    return _make



@pytest.fixture
def make_submission_messages():
    def _make(
            members: list[MagicMock],
            channel_id:int,
            challenge_end_date: datetime
    ):

        used_ids = set()
        messages = []

        for member in members:
            message_id = random.randint(100_000_000, 999_999_999)
            while message_id in used_ids:
                message_id = random.randint(100_000_000, 999_999_999)
            
            used_ids.add(message_id)
            submission_message = make_submission_message(author=member, channel_id=channel_id, id=message_id, created_at=challenge_end_date - timedelta(days=1))
            messages.append(submission_message)
        
        return sorted(messages, key=lambda message: message.id)
    
    return _make

             


@pytest.fixture
def make_monthly_submission_messages():
    def _make(
            members: list[MagicMock],
            thread_ids :list[int],
            challenge_end_date: datetime
    ):

        used_ids = set()
        messages = []
    
        for member in members:
            thread_id = random.choice(thread_ids)
            for _ in range(1, random.randint(1,5)):
                message_id = random.randint(100_000_000, 999_999_999)
                while message_id in used_ids:
                    message_id = random.randint(100_000_000, 999_999_999)
                
                used_ids.add(message_id)
                submission_message = make_submission_message(author=member, channel_id=thread_id, id=message_id, created_at=challenge_end_date - timedelta(days=1))
                messages.append(submission_message)
        
        return sorted(messages, key=lambda message: message.id)
    
    return _make






@pytest.fixture
async def seeded_monthly_challenge_data(test_config, make_monthly_submission_messages, seeded_members):
    channel_id=23432423

    thread_message_ids = [234242432, 12314324, 45646, 435645, 4354546]
    threads = []    
    challenge_end_date = datetime(year=2026, month=4, day=1, tzinfo=UTC)

    submission_messages = make_monthly_submission_messages(
            members=seeded_members.all,
            thread_ids=thread_message_ids,
            challenge_end_date=challenge_end_date
        )

    start_date = datetime(year=2026, month=3, day=1, tzinfo=UTC)
    ends_at = datetime(year=2026, month=4, day=1, tzinfo=UTC)
    day = 1
    for thread_message_id in thread_message_ids:
        _messages = [msg for msg in submission_messages if msg.channel.id == thread_message_id]
        thread = make_thread(name=f"DAY {day} (0{day}.03.2026) TEST CHALLENGE",parent_id=channel_id,id=thread_message_id, owner_id=test_config.admin_id, messages=_messages, created_at=start_date + timedelta(days=day))
        thread_starter_message = make_message(
        id=thread_message_id, author=MagicMock(id=test_config.admin_id),
        content=f"DAY {day} (0{day}.03.2026) TEST CHALLENGE")
        thread.fetch_message = AsyncMock(return_value=thread_starter_message)
        threads.append(thread)
        day += 1


    channel = make_text_channel(id=channel_id, threads=[threads[1]], archived_threads=[threads[0], threads[2], threads[3], threads[4]])

    return MonthlyChallengeSyncData(
        challenge_title= "01_03_2026_monthly_challenge",
        challenge_id=thread_message_ids[0],
        submission_messages=submission_messages,
        threads=threads,
        submission_channel=channel,
        starts_at=threads[0].created_at,
        ends_at=ends_at
    )



@pytest.fixture
async def seeded_monthly_challenge(uow, seeded_monthly_challenge_data):
    challenge_data = MonthlyChallengeData(
        id=seeded_monthly_challenge_data.challenge_id,
        title=seeded_monthly_challenge_data.challenge_title,
        is_active=True,
        starts_at=seeded_monthly_challenge_data.starts_at,
        ends_at=seeded_monthly_challenge_data.ends_at
    )

    await uow.challenges.create_or_update_monthly_challenge(data=challenge_data)
    submissions = {(msg.author.id, msg.channel.id):{
            "id":msg.id,
            "title":"test_title",
            "author_id":msg.author.id,
            "thread_id":msg.channel.id,
            "challenge_id":seeded_monthly_challenge_data.challenge_id,
            "created_at":msg.created_at,
            "edited_at":msg.edited_at
        } for msg in seeded_monthly_challenge_data.submission_messages}

        

    await uow.challenges.bulk_insert_monthly_submissions(submissions=submissions.values())

    return seeded_monthly_challenge_data




@pytest.fixture
async def seeded_empty_challenge(mock_bot,
    uow,

    make_challenge_data,

    ):
    challenge_message = make_message(id=12345, embeds=[MagicMock(spec=Embed)])
    challenge_info_channel = make_text_channel(id=111, messages=[challenge_message])

    challenge_data = make_challenge_data(
            id=challenge_message.id,
            title="test_sync_challenge_data_title",
            description="test_sync_challenge_data_description",
            is_ongoing_voting=True,
            is_active=True,
            starts_at=datetime(year=2026, month=3, day=10, tzinfo=UTC),
            ends_at=datetime(year=2026, month=3, day=20, tzinfo=UTC),
            type="official"
        )
    challenge = await uow.challenges.create_or_update(data=challenge_data)
    return challenge
    


@pytest.fixture
async def seeded_challenge(
    mock_bot,
    uow,
    seeded_members,
    make_challenge_data,
    make_submission_messages
    ):
    challenge_message = make_message(id=12345, embeds=[MagicMock(spec=Embed)])
    challenge_info_channel = make_text_channel(id=111, messages=[challenge_message])

    challenge_data = make_challenge_data(
            id=challenge_message.id,
            title="test_sync_challenge_data_title",
            description="test_sync_challenge_data_description",
            is_ongoing_voting=True,
            is_active=True,
            starts_at=datetime(year=2026, month=3, day=10, tzinfo=UTC),
            ends_at=datetime(year=2026, month=3, day=20, tzinfo=UTC),
            type="official"
        )
    
    

    submission_messages = make_submission_messages(
    members=seeded_members.all,
    channel_id=mock_bot.config.official_submission_channel_id,
    challenge_end_date=datetime(year=2026, month=3, day=20, tzinfo=UTC))

    submission_channel = make_text_channel(
    id=mock_bot.config.official_submission_channel_id,
    messages=submission_messages)

    challenge = await uow.challenges.create_or_update(data=challenge_data)

    return ChallengeSyncData(
        existing_users=seeded_members,
        challenge_data=challenge_data,
        challenge=challenge,
        submission_messages=submission_messages,
        votes=[],
        winners=[],

        submission_channel=submission_channel,
        challenge_info_channel=challenge_info_channel

    )

@pytest.fixture
async def seeded_members(uow,make_members):
    members = make_members(10, 5)

    for member in members:
        user_data = UserData(
            id=member.id,
            username=member.name,
            display_name=member.display_name,
            is_purge_data=True
        )
        await uow.users.create(user_data)

    seeded_members_data = {f"user{i}":user for i, user in enumerate(members)}

    return MemberCollection(
        **seeded_members_data
        
    )
    
@pytest.fixture
def make_challenge_messages():
    def _make(
        n:int = 1,
        created_at:datetime = datetime(year=2026, month=3, day=3)):
        author = MagicMock(id=155149108183695360) #dyno bot id to simulate
        ids = random.sample(range(100_000_000, 999_999_999), k=n)

        messages = [make_message(
            id=id,
            author=author,
            embeds=[MagicMock(spec=Embed)],
            created_at=created_at
        )for id in ids]

        return sorted(messages, key=lambda m: m.created_at)
        
    
    return _make
@pytest.fixture
def seeded_challenge_info_channel(make_challenge_messages):
    challenge_messages = make_challenge_messages(n=5)
    channel = make_text_channel(messages=challenge_messages)
    return channel


@pytest.fixture
def make_challenge_data():
    def _make(
            id:int,
            title: str = "test_title",
            description: str = "test_description",
            starts_at: datetime = datetime(year=2026, month=2, day=1, tzinfo=UTC),
            ends_at: datetime = datetime(year=2026, month=2, day=8, tzinfo=UTC),
            is_ongoing_voting: bool = True,
            is_active: bool = True,
            type: str = "official"
    ):
        challenge_data = {
            "title":title,
            "task description":description,
            "challenge duration":f"<t:{int(starts_at.timestamp())}> - <t:{int(ends_at.timestamp())}>"
        }

        challenge_embed_data = ChallengeEmbedData(
            title=challenge_data["title"],
            description=challenge_data["task description"],
            field_names=list(challenge_data.keys()),
            field_values=list(challenge_data.values()),
            id=id,
            is_active=is_active,
            is_ongoing_voting=is_ongoing_voting,
            type=type,
            duration=ChallengeDurationData(
                starts_at=starts_at,
                ends_at=ends_at,
                voting_ends_at=ends_at + timedelta(days=1)
            )
        )
        return challenge_embed_data
    
    return _make



@pytest.fixture
def make_extractor():
    def _make(
            return_value: ChallengeEmbedData
    ):
        extractor = MagicMock()
        extractor.extract_embed_data = AsyncMock(return_value=return_value)

        return extractor
    
    return _make


@pytest.fixture
async def seeded_threads():
    def _make(
        feedback_messages: list,
        track_messages: list ,   
        page_size: int = 100):
        threads = []
        for message in track_messages:
            thread_feedbacks = [
                fb for fb in feedback_messages 
                if fb.channel.id == message.id
            ]
            thread = make_thread(
                id=message.id,
                page_size=page_size,
                name=f"{message.author.name}'s thread",
                archived=random.choice([True, False]),
                parent_id=message.channel.id,
                owner_id=message.author.id,
                starter_message=message,
                messages=thread_feedbacks
            )
            threads.append(thread)
        seeded_threads_data = {f"thread{i}":thread for i,thread in enumerate(threads)} 

        return ThreadCollection(
            **seeded_threads_data
        )
    return _make

@pytest.fixture
async def seeded_feedback_messages(uow, seeded_members, seeded_track_messages, make_feedback_messages):
    feedback_messages = make_feedback_messages(seeded_members.all, seeded_track_messages.all)
    feedbacks = []
    for message in feedback_messages:
        data = {
            "id": message.id,
            "author_id": message.author.id,
            "content":message.content,
            "thread_id":message.channel.id,
            "channel_id":message.channel.parent_id,
            "track_id":message.channel.id,
            "word_count":len(message.content.split()),
            "created_at":message.created_at
        }
        feedbacks.append(data)

    seeded_feedback_messages_data = {f"feedback{i}":feedback for i,feedback in enumerate(feedback_messages)}

    await uow.feedback.bulk_insert_feedback(feedbacks)

    return FeedbackMessageCollection(
        **seeded_feedback_messages_data
    )




@pytest.fixture
async def seeded_track_messages(uow, seeded_members, make_track_messages):
    track_messages = make_track_messages(
        authors=seeded_members.all,
        channel_id=111,

    )
    
    tracks = []

    for track_message in track_messages:
        tracks.append(
            {
                "id":track_message.id,
                "author_id":track_message.author.id,
                "thread_id":track_message.id,
                "channel_id":111,
                "created_at":track_message.created_at,
                "title":"test_track1",
                "platform":"test_platform"
            }
        )

    await uow.tracks.bulk_insert_track(tracks)
    
    seeded_tracks = {f"track{i}":track for i, track in enumerate(track_messages)}
    return TrackMessageCollection(
        **seeded_tracks
    )


    
