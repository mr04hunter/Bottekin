import os
from discord import Object
from dotenv import load_dotenv
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path

load_dotenv()
from functools import lru_cache

@lru_cache(maxsize=1)
def get_word_list() -> frozenset[str]:
    env = os.getenv("ENVIRONMENT")
    path = os.getenv("WORDS_PATH", "words.txt") if env == "production" else "words.txt"
    if not os.path.exists(path):
        return frozenset()
    with open(path) as f:
        return frozenset(w.strip().lower() for w in f)

class Config(BaseSettings):
    discord_token: str = Field(default=...)
    spotify_api_client_id: str = Field(default=...)
    spotify_api_client_secret: str = Field(default=...)


    db_url: str = Field(default=...)
    db_mig_url: str = Field(default=...)
    db_health_url: str = Field(default=...)
    db_host: str = Field(default=...)
    db_name: str = Field(default=...)
    db_password: str = Field(default=...)
    db_port: str = Field(default=...)
    db_user: str = Field(default=...)

    fb_channel_ids: str = Field(default=...)
    link_channel_ids: str = Field(default=...)
    attachment_channel_ids: str = Field(default=...)
    submission_channels: str = Field(default=...)

    developer_id: int = Field(default=...)

    challenge_role_three_id: int = Field(default=...)
    challenge_role_ten_id: int = Field(default=...)
    challenge_role_thirty_id: int = Field(default=...)
    challenge_role_fifty_id: int = Field(default=...)
    challenge_role_hundred_id: int = Field(default=...)

    feedback_role_fifteen_id: int = Field(default=...)
    feedback_role_thirty_id: int = Field(default=...)
    feedback_role_fifty_id: int = Field(default=...)
    feedback_role_hundred_id: int = Field(default=...)
    feedback_role_thousand_id: int = Field(default=...)


    challenge_info_channel_id: int = Field(default=...)
    commands_channel_id: int = Field(default=...)
    leaderboards_channel_id: int = Field(default=...)
    official_submission_channel_id: int = Field(default=...)
    rules_channel_id: int = Field(default=...)
    rules_message_id: int = Field(default=...)
    tiny_submission_channel_id: int = Field(default=...)
    winners_hall_channel_id: int = Field(default=...)
    tracks_no_feedback_channel_id: int = Field(default=...)
    guild_id: int = Field(default=...)


    dyno_id: int = Field(default=...)
    admin_id: int = Field(default=...)
    bot_id: int = Field(default=...)
    dc_webhook: str = Field(default=...)

    log_path: str = "logs/discord_bot.log"
    log_level: str = "INFO"



    @property
    def feedback_roles(self) -> dict[int, Object]:
        return {
        15: Object(id=self.feedback_role_fifteen_id),
        30: Object(id=self.feedback_role_thirty_id),
        50: Object(id=self.feedback_role_fifty_id),
        100: Object(id=self.feedback_role_hundred_id),
        1000: Object(id=self.feedback_role_thousand_id)
        }
    
    @property
    def challenge_roles(self) -> dict[int, Object]:
        return {
        3: Object(id=self.challenge_role_three_id),
        10: Object(id=self.challenge_role_ten_id),
        30: Object(id=self.challenge_role_thirty_id),
        50: Object(id=self.challenge_role_fifty_id),
        100: Object(id=self.challenge_role_hundred_id),
        }

    @property
    def challenge_role_ids(self) -> list[int]:
        return [self.challenge_role_three_id, self.challenge_role_ten_id,
                self.challenge_role_thirty_id, self.challenge_role_fifty_id,
                self.challenge_role_hundred_id]
    
    @property
    def feedback_role_ids(self) -> list[int]:
        return [self.feedback_role_fifteen_id, self.feedback_role_thirty_id,
                self.feedback_role_fifty_id, self.feedback_role_hundred_id,
                self.feedback_role_thousand_id]

    @property
    def feedback_channel_ids(self) -> list[int]:
        return [int(x) for x in self.fb_channel_ids.split(",") if x]

    @property
    def feedback_link_channel_ids(self) -> list[int]:
        return [int(x) for x in self.link_channel_ids.split(",") if x]

    @property
    def feedback_attachment_channel_ids(self) -> list[int]:
        return [int(x) for x in self.attachment_channel_ids.split(",") if x]

    @property
    def submission_channel_ids(self) -> list[int]:
        return [int(x) for x in self.submission_channels.split(",") if x]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            raise ValueError(f"log_level must be one of {valid}, got {v!r}")
        return v.upper()


class DevConfig(Config):
    model_config = {
        "env_file": ".env",
        "extra":"ignore",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


class ProdConfig(Config):
    model_config = {
        "secrets_dir": "/run/secrets",
        "case_sensitive": False,
    }


def load_config() -> Config:
    if os.getenv("ENVIRONMENT") == "production" or Path("/run/secrets").exists():
        return ProdConfig(
            log_path="/app/logs/discord_bot.log",
            log_level="INFO"
        )
    return DevConfig()


config = load_config()