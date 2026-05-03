"""
Centralized logging configuration using loguru.
Provides logger instances for different bot subsystems.
"""
from loguru import logger
import logging
import sys
from typing import TYPE_CHECKING
from .decorators import log_function, log_slash_command, link_extractor_logger

if TYPE_CHECKING:
    from loguru import Logger

from bot.config import config


def setup_logging() -> "Logger":
    """
    Configure loguru for JSON + console output.
    Call this ONCE at bot startup.
    """
    logger.remove()

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level=config.log_level,
        colorize=True,
        enqueue=True
    )

    logger.add(
        config.log_path,
        level=config.log_level,
        rotation="100 MB",
        retention="7 days",
        enqueue=True,
        serialize=True,
        backtrace=False,
        diagnose=False
    )


    _setup_stdlib_interception()
    

    _silence_discord_salchemy_loggers()

    return logger


def _setup_stdlib_interception():
    """Redirect standard library logging to loguru"""
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            logger.opt(depth=6, exception=record.exc_info).log(
                level, record.getMessage()
            )

    root_logger = logging.getLogger()
    

    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    
    root_logger.handlers = [InterceptHandler()]
    root_logger.setLevel(
        logging.INFO if config.log_level == "INFO" else logging.DEBUG
    )


def _silence_discord_salchemy_loggers():
    """Prevent discord.py from spamming logs"""
    for logger_name in ["discord", "discord.client", "discord.gateway", "discord.http"]:
        logging.getLogger(logger_name).propagate = False

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

def get_logger(name: str) -> "Logger":
    """
    Get a context-aware logger for a specific subsystem.
    
    Usage:
        from bot.logging import get_logger
        logger = get_logger('feedback')
        logger.info("Processing feedback")
    
    Args:
        name: Subsystem name (e.g., 'feedback', 'challenge', 'link_extractor')
    
    Returns:
        Logger instance bound with the subsystem name
    """
    return logger.bind(subsystem=name)


__all__ = ['setup_logging', 'get_logger', 'logger']