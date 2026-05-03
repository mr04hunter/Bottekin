from typing import Protocol, runtime_checkable
from bot.registry.channel_registry import ChannelRegistry
import discord
from bot.integrations.discord.client import DcClient


@runtime_checkable
class ChannelProvider(Protocol):
    channels: ChannelRegistry
    guild: discord.Guild
    client: DcClient

@runtime_checkable
class ClientProvider(Protocol):
    channels: ChannelRegistry
    guild: discord.Guild
    client: DcClient

