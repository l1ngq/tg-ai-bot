from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone

import feedparser
import httpx

from bot.utils.errors import UserVisibleError

logger = logging.getLogger(__name__)

RSS_URLS = [
    "https://habr.com/ru/rss/hub/devops/all/",
    "https://habr.com/ru/rss/hub/artificial_intelligence/all/",
    "https://habr.com/ru/rss/hub/linux/all/",
    "https://habr.com/ru/rss/hub/sys_admin/all/",
]


async def _fetch_feed(url: str, client: httpx.AsyncClient) -> feedparser.FeedParserDict:
    response = await client.get(url, timeout=20.0, follow_redirects=True)
    response.raise_for_status()
    return feedparser.parse(response.text)


def _entry_datetime(entry: feedparser.FeedParserDict) -> datetime | None:
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published:
        return None
    return datetime.fromtimestamp(time.mktime(published), tz=timezone.utc)


async def get_habr_articles() -> dict:
    try:
        async with httpx.AsyncClient() as client:
            feeds = await asyncio.gather(
                *[_fetch_feed(url, client) for url in RSS_URLS]
            )

        now = datetime.now(timezone.utc)
        articles = []
        for feed in feeds:
            for entry in feed.entries:
                published_at = _entry_datetime(entry)
                if not published_at:
                    continue
                if now - published_at > timedelta(hours=24):
                    continue
                articles.append(
                    {
                        "title": (entry.get("title") or "").strip(),
                        "link": (entry.get("link") or "").strip(),
                        "summary": (entry.get("summary") or "").strip(),
                        "published": published_at,
                    }
                )

        articles.sort(key=lambda item: item["published"], reverse=True)
        result = [
            {
                "title": article["title"],
                "link": article["link"],
                "summary": article["summary"],
                "published": article["published"].isoformat(),
            }
            for article in articles[:5]
        ]

        if not result:
            return {
                "ok": True,
                "articles": [],
                "message": "За последние 24 часа новых статей не найдено",
            }

        return {"ok": True, "articles": result}
    except Exception:
        logger.exception("Habr fetch error")
        raise UserVisibleError("Не удалось получить статьи с Habr. Попробуйте позже.")
