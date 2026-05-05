import asyncio
import logging
from datetime import datetime

from github import Github

from bot.utils.errors import UserVisibleError
from bot.utils.sanitize import build_note_filename

logger = logging.getLogger(__name__)


def _add_note_sync(
    token: str,
    owner: str,
    repo_name: str,
    branch: str,
    title: str,
    content: str,
) -> dict:
    github = Github(token)
    repo = github.get_repo(f"{owner}/{repo_name}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = build_note_filename(title, timestamp)
    path = f"00 Inbox/{filename}"
    commit_message = f"Add note: {title}"
    repo.create_file(path=path, message=commit_message, content=content, branch=branch)
    return {
        "ok": True,
        "message": f"Заметка сохранена: {path}",
        "path": path,
        "filename": filename,
    }


async def add_note(
    token: str,
    owner: str,
    repo_name: str,
    branch: str,
    title: str,
    content: str,
) -> dict:
    try:
        return await asyncio.to_thread(
            _add_note_sync, token, owner, repo_name, branch, title, content
        )
    except Exception:
        logger.exception("GitHub API error")
        raise UserVisibleError("GitHub не отвечает. Попробуйте позже.")
