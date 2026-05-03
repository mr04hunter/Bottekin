from datetime import UTC, datetime
import pytest
from bot.types.tests.track import UserLeftNotifCollection
from bot.types.tests.user import UserCollection

@pytest.fixture
async def seeded_users_to_delete(
    make_user
) -> UserCollection:
    user1 = await make_user(user_id=999, username="user1", display_name="user_display_name1", created_at=datetime(year=2026, month=1, day=2, tzinfo=UTC))
    user2 = await make_user(user_id=998, username="user2", display_name="user_display_name2", created_at=datetime(year=2026, month=1, day=3, tzinfo=UTC))
    user3 = await make_user(user_id=997, username="user3", display_name="user_display_name3", created_at=datetime(year=2026, month=1, day=5, tzinfo=UTC))


    
    
    return UserCollection(
        user1=user1,
        user2=user2,
        user3=user3,
    )


@pytest.fixture
async def seeded_user_left_notification_messages(uow,seeded_users):
    await uow.tracks.add(
            {
                "id":888888,
                "thread_id":888888,
                "author_id":seeded_users.track_author1.id,
                "title":"test_title",
                "channel_id":11123453,
                "platform":"test_platform"
            }
        )

    await uow.tracks.add(
        {
            "id":999999,
            "thread_id":999999,
            "author_id":seeded_users.track_author1.id,
            "title":"test_title",
            "channel_id":113453123,
            "platform":"test_platform"
        }
    )

    await uow.tracks.add(
        {
            "id":55555,
            "thread_id":55555,
            "author_id":seeded_users.track_author1.id,
            "title":"test_title",
            "channel_id":11345345123,
            "platform":"test_platform"
        }
    )

    notif1 = await uow.tracks.create_user_left_notif_message(user_id=seeded_users.track_author1.id, message_id=11111111, channel_id=22222232222)
    notif2 = await uow.tracks.create_user_left_notif_message(user_id=seeded_users.track_author1.id, message_id=22222222, channel_id=23233232)
    notif3 = await uow.tracks.create_user_left_notif_message(user_id=seeded_users.track_author1.id, message_id=33333333, channel_id=22222333332222)

    return UserLeftNotifCollection(
        notif1=notif1,
        notif2=notif2,
        notif3=notif3
    )