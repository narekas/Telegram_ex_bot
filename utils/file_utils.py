import aiofiles
import json
from aiogram import Bot
from config import load_config

config = load_config()
bot = Bot(token=config.bot_token)

async def async_write_json(file_path, data):
    async with aiofiles.open(file_path, 'w') as file:
        await file.write(json.dumps([item.dict() for item in data]))

async def async_read_json(file_path, default=None):
    try:
        async with aiofiles.open(file_path, 'r') as file:
            content = await file.read()
            return json.loads(content)
    except FileNotFoundError:
        return default

async def notify_admins(text: str):
    """Функция для отправки уведомлений всем администраторам."""
    for admin_chat_id in config.admin_chat_ids:
        await bot.send_message(chat_id=admin_chat_id, text=text)
