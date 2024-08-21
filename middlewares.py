from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable, List

class AdminIDMiddleware(BaseMiddleware):
    def __init__(self, admin_chat_ids: List[int]):
        super().__init__()
        self.admin_chat_ids = admin_chat_ids

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ):
        # Проверка на администратора
        if event.from_user.id in self.admin_chat_ids:
            data['is_admin'] = True
        else:
            data['is_admin'] = False

        return await handler(event, data)
