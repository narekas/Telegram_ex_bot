from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.orm import Session
from models.order import Order
from db import Session

router = Router()


async def admin_list_orders(message: Message, admin_chat_id: int):
    if message.from_user.id != admin_chat_id:
        await message.answer("У вас нет прав для использования этой команды.")
        return

    with Session() as session:
        orders = session.query(Order).all()

    if not orders:
        await message.answer("Нет активных ордеров.")
        return

    for order in orders:
        await message.answer(f"Ордер #{order.id}:\n"
                             f"Тип: {'Продажа' if order.order_type == 'sell' else 'Покупка'}\n"
                             f"Сумма: {order.amount} USDT\nЦена: {order.price}\nПроцент: {order.percent}%\n"
                             f"Создатель: @{order.creator_username}")


def register_admin_handlers(router: Router):
    router.message.register(admin_list_orders, Command(commands=["admin_orders"]))
