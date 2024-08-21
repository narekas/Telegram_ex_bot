from aiogram import BaseMiddleware, Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from typing import Callable, Dict, Any, Awaitable

class ChatMembershipMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot, chat_id: int):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ):
        # Проверка на членство в чате
        if await self.is_member(event.from_user.id):
            return await handler(event, data)
        else:
            await event.answer("Вы не можете использовать этого бота, так как ордера создаються исключительно в боте ❗ ️")

    async def is_member(self, user_id: int) -> bool:
        try:
            chat_member = await self.bot.get_chat_member(self.chat_id, user_id)
            return chat_member.status in ["member", "administrator", "creator"]
        except TelegramBadRequest:
            return False
