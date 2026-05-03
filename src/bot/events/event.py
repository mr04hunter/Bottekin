from collections.abc import Callable
from dataclasses import dataclass
import inspect
from bot.logging import get_logger
import traceback as tb

logger = get_logger("bot_custom_event")

UPDATE_WINNERS_LEADERBOARD = "all_time_leaderboards"
UPDATE_FEEDBACK_LEADERBOARD = "fetch_and_store_feedback"
UPDATE_CURRENT_CHALLENGE_LEADERBOARD = "current_challenge_leaderboard_update"
UPDATE_SUBMISSIONS_LEADERBOARD = "submissions_leaderboard"
UPDATE_MOST_ACTIVE_PERIODS_BOARD = "update_most_active_periods_board"
UPDATE_SERVER_ACTIVITIES_BOARD = "update_server_activities_board"


CLEANUP_TRACK_WITH_NO_FEEDBACK = "cleanup_track_with_no_feedback"
SYNC_TRACK_WITH_NO_FEEDBACK = "syn_track_with_no_feedback"
DELETE_TRACK_WITH_NO_FEEDBACK = "delete_track_with_no_feedback"

SYNC_DATA = "sync_data"

SET_CHALLENGE_ROLE = "set_challenge_role"
SET_FEEDBACK_ROLE = "set_feedback_role"

# event system for assigning roles updating leaderboards

@dataclass
class BotEvent:
    callback:Callable
    once:bool  = False


class Emitter:
    def __init__(self) -> None:
        self._events: dict[str, list[BotEvent]] = {}

    def on(self, event_name: str, callback:Callable | None = None) -> Callable:
        logger.bind(
                callback=str(callback),
                event_name=event_name
            ).debug("Callback")
        def decorator(func: Callable) -> Callable:
            logger.bind(
                func=str(func)
            ).debug("Func")
            if event_name not in self._events:
                self._events[event_name] = []
            
            event = BotEvent(callback=func)
            self._events[event_name].append(event)
            return func
        
        return decorator if callback is None else decorator(callback)
    
    async def emit_async(self, event_name:str, *args, **kwargs) -> None:
        bot_event_handlers = self._events.get(event_name,[]).copy()
        to_remove = []

        logger.bind(
            bot_event_handlers=[str(event_handler.callback) for event_handler in bot_event_handlers],
            event_name=event_name,
            args=str(args),
            kwargs=str(kwargs)
        ).debug("Emit")
        for handler in bot_event_handlers:
            try:
                logger.bind(
                    handler=str(handler)
                ).debug("Event handler debug")

                if inspect.iscoroutinefunction(handler.callback):
                    await handler.callback(*args,**kwargs)
                else:
                    handler.callback(*args, **kwargs)
                
                
            except Exception as e:
                logger.bind(
                    error=str(e),
                    tb=str(tb)
                ).error("Error on emmit")

            if handler.once:
                to_remove.append(handler)


        for handler in to_remove:
            self._events[event_name].remove(handler)
    




def create_event_handler() -> Emitter:
    return Emitter()