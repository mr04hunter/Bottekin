from dataclasses import dataclass
import random
from unittest.mock import MagicMock

from discord import Message, Thread
from bot.database.models import User, Track, TrackWithNoFeedback, UserLeftNotificationMessage
from bot.types.tests.collections import Collection
from collections import Counter
from datetime import datetime

class TrackCollection(Collection[Track]):
    @property
    def total_tracks(self):
        return len([track for track in self._items.values()])
    def get_tracks_of_user(self, user_id:int):
        return [track for track in self._items.values() if isinstance(track, Track) and track.author_id==user_id]
    def get_total_tracks_of_user(self, user_id):
        return len([track for track in self._items.values() if track.author_id==user_id])
    def get_all_tracks_created_at(self, created_at:datetime):
        return [track for track in self._items.values() if isinstance(track, Track) and track.created_at==created_at]
    
class UserLeftNotifCollection(Collection[UserLeftNotificationMessage]): pass

class TrackMessageCollection(Collection[Message]):
    @property
    def total_tracks(self):
        return len([track for track in self._items.values()])
    def get_tracks_of_user(self, user_id:int):
        return [track for track in self._items.values() if isinstance(track, Message) and track.author.id==user_id]
    def get_total_tracks_of_user(self, user_id):
        return len([track for track in self._items.values() if track.author.id==user_id])
    @property
    def author_track_ids(self):
        return {message.id:message.author.id for message in self._items.values()}
    
class ThreadCollection(Collection[MagicMock]):
    @property
    def total_threads(self):
        return len([thread for thread in self._items.values()])
    def get_tracks_of_user(self, user_id:int):
        return [thread for thread in self._items.values() if isinstance(thread, Thread) and thread.owner_id==user_id]
    def get_total_tracks_of_user(self, user_id):
        return len([thread for thread in self._items.values() if thread.owner_id==user_id])

    def get_total_feedbacks(self):
        feedbacks = []
        for thread in self._items.values():
            authors_in_thread = set()
            for message in thread.messages:
                if message.author.id != thread.owner_id and message.author.id not in authors_in_thread:
                    feedbacks.append(message)
                    authors_in_thread.add(message.author.id)

        return len(feedbacks)
    
    def get_feedbacks_on_thread(self, thread_id):
        threads = {thread.id:thread for thread in self._items.values()}
        thread = threads.get(thread_id)
        if not thread:
            return None
        
        return thread.messages
    

    def get_all_feedbacks(self):
        feedbacks = []
        for thread in self._items.values():
            authors_in_thread = set()
            for message in thread.messages:
                if message.author.id != thread.owner_id and message.author.id not in authors_in_thread:
                    feedbacks.append(message)
                    authors_in_thread.add(message.author.id)

        return feedbacks
    
    def select_random_fb_author(self):
        feedback = random.choice(self.get_all_feedbacks())

        return feedback.author

    def get_feedbacks_of_user(self, user_id):
        feedbacks = [feedback for feedback in self.get_all_feedbacks() if feedback.author.id == user_id]

        return feedbacks
    
    def set_page_size(self, page_size:int):
        for thread in self._items.values():
            thread.page_size = page_size



class TrackWithNoFeedbackCollection(Collection[TrackWithNoFeedback]): pass