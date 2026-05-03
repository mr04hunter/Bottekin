from dataclasses import dataclass

from discord import Member
from bot.database.models import User, Submission, Challenge, Vote, Winner, Feedback, Track, TrackWithNoFeedback
from typing import Any, TypeVar, Generic

T = TypeVar("T")

class Collection(Generic[T]):
    def __init__(self, **kwargs: T):
        self._items: dict[str, T] = kwargs

    def __getattr__(self, name: str) -> T:
        try:
            return self._items[name]
        except KeyError:
            raise AttributeError(f"{type(self).__name__} has no item '{name}'")
        

    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self._items.keys())})"

    def __iter__(self):
        return iter(self._items.values())

    def __len__(self):
        return len(self._items)
    
    @property
    def all(self):
        return [item for item in self._items.values()]
    
