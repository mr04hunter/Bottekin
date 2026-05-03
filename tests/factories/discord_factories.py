from typing import Any
from unittest.mock import AsyncMock, MagicMock
import discord
from discord import Embed
from datetime import datetime, timezone, UTC, timedelta
import random


def make_member(
    id: int = 123456789,
    name: str = "testuser",
    display_name: str = "Test User",
    bot: bool = False,
    roles: list | None = None
) -> MagicMock:
    user = MagicMock(spec=discord.Member)
    user.id = id
    user.name = name
    user.display_name = display_name
    user.mention = f"<@{id}>"
    user.bot = bot
    user.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.display_avatar = MagicMock()
    user.display_avatar.url = "https://cdn.discordapp.com/fake-avatar.png"
    user.roles = roles or []
    user.add_roles = AsyncMock()
    user.remove_roles = AsyncMock()
    return user


def make_message(
    id: int = 987654321,
    content: str = "test message",
    author: MagicMock | None = None,
    channel_id: int = 111,
    attachments: list | None = None,
    reactions: list | None = None,
    embeds: list | None = None,
    thread: MagicMock | None = None,
    created_at: datetime | None = None,
    edited_at: datetime | None = None,
) -> MagicMock:
    message = MagicMock(spec=discord.Message)
    message.id = id
    message.content = content
    message.author = author or make_member()
    message.channel = make_text_channel(id=channel_id)
    message.channel.id = channel_id
    message.attachments = attachments or []
    message.reactions = reactions or []
    message.thread = thread
    message.created_at = created_at
    message.edited_at = edited_at
    message.created_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    message.jump_url = f"https://discord.com/channels/0/{channel_id}/{id}"
    message.add_reaction = AsyncMock()
    message.create_thread = AsyncMock()
    message.delete = AsyncMock()
    message.edit = AsyncMock()
    message.embeds = embeds or []
    return message



def make_text_channel(
    id: int = 111,
    name: str = "test-channel",
    guild: MagicMock | None = None,
    messages: list | None = None,
    threads: list | None = None,
    archived_threads: list | None = None,

    page_size: int = 100,

) -> MagicMock:
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = id

    channel.name = name
    channel.type = discord.ChannelType.text
    channel.guild = guild or make_guild()
    channel.send = AsyncMock()
    channel.fetch_message = AsyncMock()
    channel.messages = messages or []
    archived_threads = archived_threads or []
    channel.threads = threads or []


    def get_thread(id:int):
        if not channel.threads:
            return None
        threads = {thread.id:thread for thread in channel.threads}
        return threads.get(id)

    def history_factory(limit:int, oldest_first:bool = False, after=None, before=None):
        after_id = None
        after_dt = None
        if isinstance(after, discord.Object):
            after_id=after.id
        
        if isinstance(after, datetime):
            after_dt = after

        filtered = channel.messages

        if after_id is not None:
            filtered = [m for m in channel.messages if  m.id>after_id]

        elif after_dt is not None:
            filtered = [m for m in channel.messages if  m.created_at>after_dt]
        
        if before is not None:
            filtered = [m for m in filtered if  m.created_at<before]
        
        if not oldest_first:
            filtered = list(reversed(filtered))
    
        page = filtered[:page_size]

        async def _gen():
            for m in page:
                yield m

        return _gen()
    
    def archived_threads_factory(limit:int, oldest_first:bool = True, after=None):
        filtered = [t for t in archived_threads if after is None or t.created_at>after]

        page = filtered[:limit]

        async def _gen():
            for m in page:
                yield m

        return _gen()
    
    channel.history = MagicMock(side_effect=history_factory)
    channel.archived_threads = MagicMock(side_effect=archived_threads_factory)
    channel.get_thread = MagicMock(side_effect=get_thread)


    return channel


def make_thread(
    owner_id:int,
    starter_message: MagicMock | None = None,
    id: int = 222,
    parent_id: int = 111,
    parent: MagicMock | None = None,
    name: str = "test-thread",
    messages: list | None = None,
    type: discord.ChannelType = discord.ChannelType.public_thread,
    archived: bool = False,
    page_size: int = 100
    
) -> MagicMock:
    thread = MagicMock(spec=discord.Thread)
    thread.parent = parent or None
    thread.id = id
    thread.parent_id = parent_id
    thread.archived = archived
    thread.type = type
    thread.name = name
    thread.jump_url = f"https://discord.com/channels/0/{parent_id}/{id}"
    thread.send = AsyncMock()
    thread.delete = AsyncMock()
    thread.created_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    messages = messages or []
    thread.owner_id = owner_id
    thread.starter_message = starter_message or None
    thread.messages = messages or []

    def history_factory(limit:int, oldest_first:bool = False, after=None, before=None):
        after_id = None
        after_dt = None
        if isinstance(after, discord.Object):
            after_id=after.id
        
        if isinstance(after, datetime):
            after_dt = after

        filtered = thread.messages

        if after_id is not None:
            filtered = [m for m in thread.messages if  m.id>after_id]

        elif after_dt is not None:
            filtered = [m for m in thread.messages if  m.created_at>after_dt]
        
        if before is not None:
            filtered = [m for m in filtered if  m.created_at<before]
        
        if not oldest_first:
            filtered = list(reversed(filtered))
    
        page = filtered[:page_size]

        async def _gen():
            for m in page:
                yield m

        return _gen()
    
    thread.history = MagicMock(side_effect=history_factory)
    return thread


def make_guild(
        id: int = 999,
        members: list | None = None,
        page_size:int = 100
) -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = id
    guild.fetch_member = AsyncMock()
    guild.fetch_channel = AsyncMock()
    guild.get_channel = MagicMock(return_value=None)
    guild.members = members or []
    def members_factory(limit:int, after=None):
        filtered = [member for member in guild.members if after is None or member.created_at>after]
        page = filtered[:page_size]

        async def _gen():
            for member in page:
                yield member

        return _gen()


    guild.fetch_members = MagicMock(side_effect=members_factory)    


    return guild



def make_embed(
        fields:dict[str, Any],
        title: str = "test embed",
        description: str = "test description"
) -> MagicMock:
    embed = MagicMock(spec=Embed)
    embed.title = title
    embed.description = description
    embed.fields = fields

    return embed


def make_attachment(
    id: int = 1,
    filename: str = "track.mp3",
    title: str = "My Track - Artist",
    content_type: str = "audio/mpeg",
) -> MagicMock:
    attachment = MagicMock(spec=discord.Attachment)
    attachment.id = id
    attachment.filename = filename
    attachment.title = title
    attachment.content_type = content_type
    return attachment


def make_reaction(
    emoji: str = "👍",
    count: int = 1,
    users: list | None = None,
) -> MagicMock:
    reaction = MagicMock(spec=discord.Reaction)
    reaction.emoji = emoji
    reaction.count = count
    _users = users or []

    async def users_gen(*args, **kwargs):
        for u in _users:
            yield u

    # Call the factory each time so a fresh generator is returned
    reaction.users = MagicMock(side_effect=lambda *a, **kw: users_gen())
    return reaction


def make_raw_reaction(
    message_id: int = 987654321,
    user_id: int = 123456789,
    channel_id: int = 111,
    emoji_str: str = "👍",
    message_author_id: int | None = None,
    member: MagicMock | None = None,
) -> MagicMock:
    payload = MagicMock(spec=discord.RawReactionActionEvent)
    payload.message_id = message_id
    payload.user_id = user_id
    payload.channel_id = channel_id
    payload.emoji = MagicMock()
    payload.emoji.__str__ = lambda self: emoji_str
    payload.message_author_id = message_author_id or user_id + 1
    payload.member = member
    return payload


def make_submission_message(
    id: int = 111222333,
    author: MagicMock = MagicMock(id=213123),
    channel_id: int = 1004,
    content: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    created_at: datetime | None = None,
    attachments: list | None = None,
    edited_at: datetime | None = None,
    title:str="test_submission"
) -> MagicMock:


    message = MagicMock(spec=discord.Message)
    message.id = id
    message.content = content
    message.attachments = attachments or []
    message.reactions = []
    message.edited_at = edited_at
    message.created_at = created_at or datetime(2026, 1, 1, tzinfo=timezone.utc)
    message.title = title
    message.author = author

    channel = MagicMock(spec=discord.TextChannel)
    channel.id = channel_id or 1004
    channel.type = discord.ChannelType.text
    message.channel = channel

    message.jump_url = f"https://discord.com/channels/0/{channel.id}/{id}"
    message.add_reaction = AsyncMock()
    message.delete = AsyncMock()

    return message

def make_track_message(
    author: MagicMock,
    channel_id: int,
    message_id: int | None = None,
) -> MagicMock:
    mid = message_id or random.randint(100_000_000, 999_999_999)
    msg = MagicMock(spec=discord.Message)
    msg.id = mid
    msg.author = author
    msg.content = f"https://www.youtube.com/watch?v={''.join(random.choices('abcdefghij', k=11))}"
    msg.attachments = []
    msg.reactions = []
    msg.edited_at = None
    msg.created_at = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(seconds=mid % 100_000)

    channel = MagicMock(spec=discord.TextChannel)
    channel.id = channel_id
    channel.type = discord.ChannelType.text
    msg.channel = channel

    thread = MagicMock(spec=discord.Thread)
    thread.id = mid  # thread_id == message_id convention
    msg.thread = thread
    msg.create_thread = AsyncMock(return_value=thread)
    msg.add_reaction = AsyncMock()
    return msg

def make_feedback_message(
    content: str,
    author: MagicMock,
    channel_id: int,
    channel_parent_id:int,
    message_id: int | None = None,
) -> MagicMock:
    mid = message_id or random.randint(100_000_000, 999_999_999)
    msg = MagicMock(spec=discord.Message)
    msg.id = mid
    msg.author = author
    msg.content = content
    msg.attachments = []
    msg.reactions = []
    msg.edited_at = None
    msg.created_at = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(seconds=mid % 100_000)

    channel = MagicMock(spec=discord.TextChannel)
    channel.id = channel_id
    channel.parent_id = channel_parent_id
    channel.type = discord.ChannelType.text
    msg.channel = channel
    

    msg.add_reaction = AsyncMock()
    return msg