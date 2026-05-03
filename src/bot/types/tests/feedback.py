from dataclasses import dataclass
from datetime import datetime

from discord import Message
from bot.database.models import Feedback, User, Track
from bot.types.tests.collections import Collection

    

class FeedbackCollection(Collection[Feedback]):
    @property
    def total_feedbacks(self):
        return len([feedback for feedback in self._items.values() if isinstance(feedback, Feedback)])
    @property
    def total_feedback_words(self):
        return sum([feedback.word_count for feedback in self._items.values() if isinstance(feedback, Feedback)])
    
    def get_feedbacks_of_user(self, user_id:int):
        return [feedback for feedback in self._items.values() if isinstance(feedback, Feedback) and feedback.author_id==user_id]

    def get_total_feedbacks_of_user(self, id: int):
        return len([feedback for feedback in self._items.values() if isinstance(feedback, Feedback) and feedback.author_id==id])
    
    def get_total_fb_words_of_user(self, id: int):
        return sum([feedback.word_count for feedback in self._items.values() if isinstance(feedback, Feedback) and feedback.author_id==id])
    
    def get_all_feedbacks_created_at(self, created_at:datetime):
        return [feedback for feedback in self._items.values() if isinstance(feedback, Feedback) and feedback.created_at==created_at]
    

class FeedbackMessageCollection(Collection[Message]):
    @property
    def total_feedbacks(self):
        return len([feedback_message for feedback_message in self._items.values() if isinstance(feedback_message, Message)])

    def get_feedbacks_of_user(self, user_id:int):
        return [feedback_message for feedback_message in self._items.values() if isinstance(feedback_message, Message) and feedback_message.author.id==user_id]

    def get_total_feedbacks_of_user(self, id: int):
        return len([feedback_message for feedback_message in self._items.values() if isinstance(feedback_message, Message) and feedback_message.author.id==id])
    