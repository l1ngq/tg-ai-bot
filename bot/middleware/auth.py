from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message, TelegramObject


Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class AuthMiddleware(BaseMiddleware):
    def __init__(self, allowed_user_id: int) -> None:
        super().__init__()
        self.allowed_user_id = allowed_user_id

    async def __call__(
        self,
        handler: Handler,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.chat.type != ChatType.PRIVATE:
                return None
            if event.from_user is None or event.from_user.id != self.allowed_user_id:
                return None

        return await handler(event, data)
