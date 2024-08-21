from aiogram import Router, types, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from models.order import Order, OrderType
from db import Session
from config import load_config
from utils.file_utils import notify_admins
from handlers.commands import OrderStates
from aiogram.fsm.context import FSMContext
import asyncio

router = Router()
config = load_config()
bot = Bot(token=config.bot_token)

async def remove_accept_button_after_timeout(message: types.Message, order_id: int, timeout: int = 7200):
    await asyncio.sleep(timeout)
    with Session() as session:
        order = session.query(Order).filter(Order.id == order_id).first()
        if order and not order.is_accepted:
            await message.edit_reply_markup(reply_markup=None)

async def handle_confirm_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])

    with Session() as session:
        order = session.query(Order).filter(Order.id == order_id).first()

    if order:
        order_type_text = 'Продажу' if order.order_type == OrderType.SELL else 'Покупку'

        await callback.message.edit_reply_markup(reply_markup=None)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Согласиться", callback_data=f"accept_{order.id}")]
        ])

        message = await bot.send_message(
            chat_id=config.chat_id,
            text=(f"Новый ордер #{order.id} на {order_type_text}:\n"
                  f"Сумма: {order.amount} USDT💵\nПроцент: {order.percent}%\n"
                  f"Создатель: @{order.creator_username}"),
            reply_markup=keyboard
        )

        # Уведомляем администратора о создании ордера
        await notify_admins(
            text=(f"Создан новый ордер #{order.id}:\n"
                  f"Тип: {order_type_text}\n"
                  f"Сумма: {order.amount} USDT💵\nПроцент: {order.percent}%\n"
                  f"Создатель: @{order.creator_username}")
        )

        # Уведомляем пользователя, что его ордер отправлен
        await bot.send_message(
            chat_id=callback.from_user.id,
            text="Ваш ордер был успешно отправлен в группу✅"
        )

        # Запуск задачи для удаления кнопки через 2 часа
        asyncio.create_task(remove_accept_button_after_timeout(message, order.id))

        # Добавление кнопки "Создать новый ордер"
        new_order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Создать новый ордер", callback_data="create_new_order")]
        ])

        await bot.send_message(
            chat_id=callback.from_user.id,
            text="Хотите создать новый ордер?",
            reply_markup=new_order_keyboard
        )

    else:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text="Ордер не найден."
        )


async def handle_delete_order(callback: CallbackQuery):
    data_parts = callback.data.split("_")

    # Проверяем, содержит ли строка необходимое количество частей
    if len(data_parts) < 3 or not data_parts[2].isdigit():
        await callback.message.answer("Произошла ошибка при обработке запроса. Неверный формат данных.")
        return

    order_id = int(data_parts[2])

    with Session() as session:
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await callback.message.answer("Ордер не найден.")
            return

        # Проверка, что пользователь, пытающийся удалить ордер, является его создателем
        if order.creator_user_id != callback.from_user.id and not callback.data.startswith("admin_delete_"):
            await callback.message.answer("Вы не можете удалить этот ордер, так как вы не являетесь его создателем.")
            return

        # Проверка, что ордер не был принят, если удаляет создатель
        if order.is_accepted and not callback.data.startswith("admin_delete_"):
            await callback.message.answer("Вы не можете удалить этот ордер, так как на него уже дали согласие.")
            return

        # Удаление ордера
        session.delete(order)
        session.commit()

        # Удаление сообщения в чате
        await callback.message.delete()

        await callback.message.answer("Ордер был удален.")

async def handle_edit_order(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[1])

    with Session() as session:
        order = session.query(Order).filter(Order.id == order_id).first()

    if order:
        await state.update_data(order_id=order.id)
        await state.set_state(OrderStates.waiting_for_amount)
        await callback.message.answer("Введите новую сумму (в USDT💵):")
    else:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text="Ордер не найден."
        )

async def handle_accept_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])

    with Session() as session:
        order = session.query(Order).filter(Order.id == order_id).first()

    if order:
        order.is_accepted = True  # Обновляем статус ордера
        session.commit()

    if order:
        order_type_text = 'Продажа' if order.order_type == OrderType.SELL else 'Покупка'

        # Уведомляем пользователя, что он согласился на ордер, и предлагаем связаться с создателем
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=(f"Вы согласились на ордер #{order.id}:\n"
                  f"Тип: {order_type_text}\n"
                  f"Сумма: {order.amount} USDT💵\n"
                  f"Процент: {order.percent}%\n\n"
                  f"Свяжитесь с создателем ордера: @{order.creator_username}")
        )

        # Уведомляем создателя ордера о том, что кто-то согласился на ордер
        await bot.send_message(
            chat_id=order.creator_user_id,
            text=(f"Пользователь @{callback.from_user.username} согласился на ваш ордер #{order.id}:\n"
                  f"Тип: {order_type_text}\n"
                  f"Сумма: {order.amount} USDT💵\nПроцент: {order.percent}%")
        )

        # Уведомляем администратора о том, что кто-то согласился на ордер
        await notify_admins(
            text=(f"Пользователь @{callback.from_user.username} согласился на ордер #{order.id}:\n"
                  f"Тип: {order_type_text}\n"
                  f"Сумма: {order.amount} USDT💵\nПроцент: {order.percent}%\n"
                  f"Создатель: @{order.creator_username}")
        )

        # Отправляем сообщение в общий чат о закрытии ордера
        await bot.send_message(
            chat_id=config.chat_id,
            text=f"Ордер #{order.id} подтвержден и закрыт для новых соглашений."
        )

        # Проверяем наличие сообщения перед редактированием
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)

    else:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text="Ордер не найден."
        )

async def handle_create_new_order(callback: CallbackQuery):
    # Начинаем процесс создания нового ордера
    await bot.send_message(
        chat_id=callback.from_user.id,
        text="Выберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Купить USDT💵", callback_data="start_buy")],
            [InlineKeyboardButton(text="Продать USDT💵", callback_data="start_sell")]
        ])
    )

def register_callback_handlers(router: Router):
    router.callback_query.register(handle_confirm_order, lambda c: c.data.startswith("confirm_"))
    router.callback_query.register(handle_delete_order, lambda c: c.data.startswith("delete_order_") or c.data.startswith("admin_delete_order_"))
    router.callback_query.register(handle_edit_order, lambda c: c.data.startswith("edit_"))
    router.callback_query.register(handle_accept_order, lambda c: c.data.startswith("accept_"))
    router.callback_query.register(handle_create_new_order, lambda c: c.data == "create_new_order")
