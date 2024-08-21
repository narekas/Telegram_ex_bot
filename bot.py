import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties
from aiogram.types import BotCommand
from config import load_config
from db import init_db
from handlers.callbacks import register_callback_handlers
from handlers.commands import register_handlers
from middlewares import AdminIDMiddleware
from chat_membership_middleware import ChatMembershipMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка конфигурации
config = load_config()

# Инициализация базы данных
init_db()

# Создание экземпляра бота с DefaultBotProperties
bot = Bot(
    token=config.bot_token,
    session=AiohttpSession(),
    default=DefaultBotProperties(parse_mode='HTML')
)

# Создание Router и Dispatcher
router = Router()
dp = Dispatcher()

# Регистрация middleware для добавления admin_chat_id
dp.message.middleware(ChatMembershipMiddleware(bot, config.chat_id))
dp.message.middleware(AdminIDMiddleware(config.admin_chat_ids))

# Регистрация обработчиков команд и callback
register_handlers(router)
register_callback_handlers(router)

# Включаем роутер в диспетчер
dp.include_router(router)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/sell", description="Создать ордер на продажу"),
        BotCommand(command="/buy", description="Создать ордер на покупку"),
        BotCommand(command="/my_orders", description="Показать мои ордера"),
        BotCommand(command="/orders", description="Показать все ордера"),
        BotCommand(command="/admin_orders", description="Показать ордера для админов"),
        BotCommand(command="/clear_orders", description='Очистить историю ордеров'),
    ]
    await bot.set_my_commands(commands)

async def on_startup(bot: Bot):
    await set_commands(bot)
    logging.info("Бот запущен и готов к работе.")

async def main():
    await on_startup(bot)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
