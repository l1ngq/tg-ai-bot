import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers.message import router as message_router
from bot.middleware.auth import AuthMiddleware
from config import load_config


async def main() -> None:
    config = load_config()
    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    bot = Bot(
        token=config.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.message.middleware(AuthMiddleware(config.allowed_user_id))
    dp.include_router(message_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
