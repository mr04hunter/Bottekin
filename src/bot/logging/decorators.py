import functools
import time
import traceback as tb
from typing import Awaitable, Callable, ParamSpec, TypeVar, cast, overload
from inspect import iscoroutinefunction

from loguru import logger
from discord import Interaction
import json
from bot.exceptions import BotException
import asyncio
import aiohttp


P = ParamSpec('P')
T = TypeVar('T')


@overload
def log_function(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]: ...

@overload
def log_function(func: Callable[P, T]) -> Callable[P, T]: ...

def log_function(func: Callable[P, Awaitable[T]] | Callable[P, T]) -> Callable:
    """
    Decorator to log function execution with timing and error handling.
    Works with both sync and async functions.

    """
    if iscoroutinefunction(func):
        awaitable_func = func
        
        @functools.wraps(awaitable_func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            func_class = (
                args[0].__class__.__name__ 
                if args and hasattr(args[0], "__class__") 
                else None
            )
            start_time = time.time()
            func_name = func.__name__
            
            logger.bind(
                parent_class=func_class,
                func_name=func_name,
            ).debug(f"{func_name} started")
            
            try:
                result = await awaitable_func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.bind(
                    parent_class=func_class,
                    func_name=func_name,
                    execution_time=f"{execution_time:.3f}s",
                    status="success"
                ).debug(f"{func_name} completed")
                
                return result  # type: ignore
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.bind(
                    parent_class=func_class,
                    func_name=func_name,
                    execution_time=f"{execution_time:.3f}s",
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=tb.format_exc()
                ).error(f"{func_name} failed")
                
                raise
        
        return async_wrapper
    
    else:
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            func_class = (
                args[0].__class__.__name__ 
                if args and hasattr(args[0], "__class__") 
                else None
            )
            start_time = time.time()
            func_name = func.__name__
            
            logger.bind(
                parent_class=func_class,
                func_name=func_name,
            ).debug(f"{func_name} started")
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.bind(
                    parent_class=func_class,
                    func_name=func_name,
                    execution_time=f"{execution_time:.3f}s",
                    status="success"
                ).debug(f"{func_name} completed")
                
                return result  # type: ignore
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.bind(
                    parent_class=func_class,
                    func_name=func_name,
                    execution_time=f"{execution_time:.3f}s",
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=tb.format_exc()
                ).error(f"{func_name} failed")
                
                raise
        
        return sync_wrapper


def log_slash_command(func: Callable[P, Awaitable[T]]) -> Callable:
    """
    Decorator for logging Discord slash command execution.
    Includes user, guild, channel context and metrics tracking.
    """
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
        if args and hasattr(args[0], '__class__') and not isinstance(args[0], Interaction):
            command_class = args[0]
            interaction = args[1]
        else:
            command_class = None
            interaction = args[0]
        
        interaction = cast(Interaction, interaction)
        start_time = time.time()
        command_name = interaction.command.name if interaction.command else func.__name__
        
        logger.bind(
            command=command_name,
            user_id=interaction.user.id,
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
        ).debug(f"Command '{command_name}' invoked")
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.bind(
                command=command_name,
                user_id=interaction.user.id,
                guild_id=interaction.guild_id,
                channel_id=interaction.channel_id,
                execution_time=f"{execution_time:.3f}s",
                status="success"
            ).debug(f"Command '{command_name}' completed")
            
            return result
            
        except BotException as e:
            execution_time = time.time() - start_time
            
            logger.bind(
                command=command_name,
                user_id=interaction.user.id,
                guild_id=interaction.guild_id,
                channel_id=interaction.channel_id,
                execution_time=f"{execution_time:.3f}s",
                status="handled_error",
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=tb.format_exc()
            ).warning(f"Command '{command_name}' failed (handled)")
            
            from bot.healthcheck import bot_commands_total
            bot_commands_total.labels(
                command_name=command_name, 
                status="handled_error"
            ).inc()
            
            raise
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.bind(
                command=command_name,
                user_id=interaction.user.id,
                guild_id=interaction.guild_id,
                channel_id=interaction.channel_id,
                execution_time=f"{execution_time:.3f}s",
                status="unexpected_error",
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=tb.format_exc()
            ).error(f"Command '{command_name}' failed (unexpected)")
            
            try:
                await interaction.followup.send(
                    content="❌ An unexpected error occurred. The issue has been logged.",
                    ephemeral=True
                )
            except:
                pass 

            from bot.healthcheck import bot_commands_total
            bot_commands_total.labels(
                command_name=command_name, 
                status="error"
            ).inc()
            
            raise
    
    return wrapper






def link_extractor_logger(func: Callable[P, Awaitable[str]]) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> str:
        exc_logger = logger.bind(
            args=str(args),
            kwargs=str(kwargs)
        )
        try:
            result = await func(*args, **kwargs)
            return result
        
        except asyncio.TimeoutError:
            exc_logger.error(f"Timeout while fetching YouTube title for url")
            return "unknown title"
        except aiohttp.ClientError as e:
            exc_logger.error(f"Network error extracting YouTube title")
            return "unknown title"
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            exc_logger.error(f"Error parsing YouTube response")
            return "unknown title"
        except Exception as e:
            exc_logger.error("Unexpected error extracting YouTube title")
            return "unknown title"
        

    return wrapper




__all__ = ['log_function', 'log_slash_command', 'link_extractor_logger']