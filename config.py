from __future__ import annotations

from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise ValueError(f"Missing required env var: {name}")
    return value


def _optional_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str
    openai_base_url: str | None
    todoist_api_token: str
    github_token: str
    github_owner: str
    github_repo: str
    github_branch: str
    allowed_user_id: int
    log_level: str


def load_config() -> Config:
    allowed_user_id_raw = _require_env("ALLOWED_USER_ID")
    try:
        allowed_user_id = int(allowed_user_id_raw)
    except ValueError as exc:
        raise ValueError("ALLOWED_USER_ID must be an integer") from exc

    return Config(
        telegram_bot_token=_require_env("TELEGRAM_BOT_TOKEN"),
        openai_api_key=_require_env("OPENAI_API_KEY"),
        openai_model=_require_env("OPENAI_MODEL"),
        openai_base_url=_optional_env("OPENAI_BASE_URL", None),
        todoist_api_token=_require_env("TODOIST_API_TOKEN"),
        github_token=_require_env("GITHUB_TOKEN"),
        github_owner=_require_env("GITHUB_OWNER"),
        github_repo=_require_env("GITHUB_REPO"),
        github_branch=_optional_env("GITHUB_BRANCH", "main") or "main",
        allowed_user_id=allowed_user_id,
        log_level=_optional_env("LOG_LEVEL", "INFO") or "INFO",
    )
