import asyncio
import logging

import httpx
from todoist_api_python.api import TodoistAPI

from bot.utils.errors import UserVisibleError

logger = logging.getLogger(__name__)

SYNC_QUICK_ADD_URLS = [
    "https://api.todoist.com/sync/v10/quick/add",
    "https://api.todoist.com/sync/v9/quick/add",
]


def _extract_task_info(task: object) -> tuple[str | None, str | None]:
    if isinstance(task, dict):
        task_id = task.get("id")
        task_content = task.get("content") or task.get("text")
        return (str(task_id) if task_id is not None else None, task_content)

    task_id = getattr(task, "id", None)
    task_content = getattr(task, "content", None)
    return (str(task_id) if task_id is not None else None, task_content)


def _add_task_sync(token: str, content: str) -> dict:
    api = TodoistAPI(token)
    task = api.add_task(content=content)
    task_id, task_content = _extract_task_info(task)
    payload: dict[str, object] = {
        "ok": True,
        "message": "Задача добавлена.",
    }
    if task_id:
        payload["task_id"] = task_id
    if task_content:
        payload["content"] = task_content
    return payload


async def _quick_add_via_sync_api(token: str, content: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    data = {"text": content}
    last_error: Exception | None = None

    async with httpx.AsyncClient() as client:
        for url in SYNC_QUICK_ADD_URLS:
            try:
                response = await client.post(
                    url,
                    data=data,
                    headers=headers,
                    timeout=20.0,
                )
                response.raise_for_status()
                payload = response.json()

                task = payload.get("item") or payload.get("task") or payload
                task_id, task_content = _extract_task_info(task)
                result: dict[str, object] = {
                    "ok": True,
                    "message": "Задача добавлена.",
                }
                if task_id:
                    result["task_id"] = task_id
                if task_content:
                    result["content"] = task_content
                return result
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response else None
                if status in (404, 410):
                    last_error = exc
                    continue
                raise

    if last_error:
        raise last_error

    raise RuntimeError("Quick Add endpoint is unavailable")


async def add_task(token: str, content: str) -> dict:
    try:
        return await _quick_add_via_sync_api(token, content)
    except Exception:
        logger.exception("Todoist Quick Add failed, fallback to add_task")

    try:
        return await asyncio.to_thread(_add_task_sync, token, content)
    except Exception:
        logger.exception("Todoist API error")
        raise UserVisibleError("Не удалось добавить задачу. Попробуйте позже.")
