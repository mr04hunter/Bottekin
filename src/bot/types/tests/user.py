from bot.types.tests.collections import Collection
from bot.database.models import User
from discord import Member

class UserCollection(Collection[User]):
    @property
    def all_ids(self):
        return [user.id for user in self._items.values() if isinstance(user, User)]
    
class MemberCollection(Collection[Member]):
    @property
    def all_ids(self):
        return [member.id for member in self._items.values() if isinstance(member, Member)]