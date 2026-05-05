from aiogram import F, Router
from aiogram.types import Message

from bot.llm.service import LLMService
from bot.utils.html_sanitize import sanitize_html
from config import load_config

router = Router()
_llm_service = LLMService(load_config())


@router.message(F.text)
async def handle_text(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        return

    response = await _llm_service.handle_text(text)
    if response:
        safe_response = sanitize_html(response)
        await message.answer(safe_response)
