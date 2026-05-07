from __future__ import annotations
import asyncio
from dataclasses import dataclass

@dataclass
class RateLimitGuards:
    reaction_fetch: asyncio.Semaphore
    message_fetch: asyncio.Semaphore
    thread_fetch: asyncio.Semaphore
    member_fetch: asyncio.Semaphore

_guards: RateLimitGuards | None = None

def init_guards() -> RateLimitGuards:
    global _guards
    _guards = RateLimitGuards(
        reaction_fetch=asyncio.Semaphore(1),
        message_fetch=asyncio.Semaphore(5),
        thread_fetch=asyncio.Semaphore(5),
        member_fetch=asyncio.Semaphore(2)
    )
    return _guards

def get_guards() -> RateLimitGuards:
    if _guards is None:
        raise RuntimeError("call init_guards() first")
    return _guards