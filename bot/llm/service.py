from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI
from pydantic import ValidationError

from bot.llm.tools import AddNoteArgs, AddTaskArgs, GetHabrArticlesArgs, TOOLS
from bot.utils.errors import UserVisibleError
from config import Config
from integrations.github_client import add_note
from integrations.habr_client import get_habr_articles
from integrations.todoist_client import add_task

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты личный ИИ-бот в Telegram. Определи тип запроса и действуй строго по правилам.

Правила классификации:
- Задача содержит призыв к действию, срок или конкретный результат. Идея или мысль — это заметка.
- Если пользователь явно просит статьи или новости, вызывай get_habr_articles.
- Если это задача, вызывай add_task.
- Если это заметка или идея, вызывай add_note.
- Если ни один инструмент не нужен, ответь обычным сообщением.

Правила аргументов:
- add_task: content = исходный текст пользователя без изменений.
- add_note: title = 3-4 слова по сути текста, без даты, времени, расширения или пути. content = исходный текст пользователя без изменений.
- get_habr_articles: без аргументов.

Форматирование:
- Разрешены только базовые HTML теги <b>, <i>, <a>.
- Markdown запрещен.

Ответы:
- Не упоминай внутренние инструменты или JSON.
- Если инструмент вернул ok=false, ответь пользователю текстом из error и не добавляй ничего.
- Если инструмент вернул message, используй его как краткий ответ.
- Для get_habr_articles: изучи summary, игнорируй HTML-теги. Формат: эмодзи + <b>Заголовок</b> — 1-2 предложения. <a href="...">Ссылка</a>
- Если статей нет, ответь: "За последние 24 часа новых статей не найдено".

Язык ответа: русский, английский допустим при необходимости.
"""

AI_UNAVAILABLE_MESSAGE = "ИИ временно недоступен. Попробуйте позже."
GENERAL_ERROR_MESSAGE = "Произошла ошибка. Попробуйте позже."
ARGUMENTS_ERROR_MESSAGE = "Не удалось обработать запрос. Попробуйте переформулировать."
TOOL_ERROR_MESSAGE = "Произошла ошибка при выполнении запроса. Попробуйте позже."


class LLMService:
    def __init__(self, config: Config) -> None:
        self.config = config
        client_kwargs: dict[str, Any] = {"api_key": config.openai_api_key}
        if config.openai_base_url:
            client_kwargs["base_url"] = config.openai_base_url
        self.client = AsyncOpenAI(**client_kwargs)
        self.model = config.openai_model

    async def handle_text(self, text: str) -> str:
        try:
            return await self._handle_text(text)
        except UserVisibleError as exc:
            return exc.message
        except Exception:
            logger.exception("Unhandled error in LLM flow")
            return GENERAL_ERROR_MESSAGE

    async def _handle_text(self, text: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
            )
        except Exception:
            logger.exception("OpenAI request failed")
            return AI_UNAVAILABLE_MESSAGE

        assistant_message = response.choices[0].message
        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        tool_messages = []
        for tool_call in assistant_message.tool_calls:
            result = await self._execute_tool_call(tool_call, text)
            if isinstance(result, str):
                return result
            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        try:
            followup = await self.client.chat.completions.create(
                model=self.model,
                messages=messages + [assistant_message] + tool_messages,
                temperature=0.2,
            )
        except Exception:
            logger.exception("OpenAI followup request failed")
            return AI_UNAVAILABLE_MESSAGE

        return followup.choices[0].message.content or ""

    async def _execute_tool_call(self, tool_call: Any, user_text: str) -> dict[str, Any] | str:
        name = tool_call.function.name
        arguments_json = tool_call.function.arguments or "{}"

        try:
            if name == "add_task":
                AddTaskArgs.model_validate_json(arguments_json)
                # Preserve original user text for Todoist per spec.
                return await add_task(self.config.todoist_api_token, user_text)
            if name == "add_note":
                args = AddNoteArgs.model_validate_json(arguments_json)
                # Preserve original user text for notes per spec.
                return await add_note(
                    token=self.config.github_token,
                    owner=self.config.github_owner,
                    repo_name=self.config.github_repo,
                    branch=self.config.github_branch,
                    title=args.title,
                    content=user_text,
                )
            if name == "get_habr_articles":
                GetHabrArticlesArgs.model_validate_json(arguments_json)
                return await get_habr_articles()
        except ValidationError:
            logger.exception("Invalid tool arguments for %s", name)
            return ARGUMENTS_ERROR_MESSAGE
        except UserVisibleError as exc:
            return exc.message
        except Exception:
            logger.exception("Tool execution failed: %s", name)
            return TOOL_ERROR_MESSAGE

        logger.error("Unknown tool name: %s", name)
        return ARGUMENTS_ERROR_MESSAGE
