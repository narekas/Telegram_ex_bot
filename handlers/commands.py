from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from models.order import Order, OrderType
from config import load_config
from sqlalchemy.orm import Session
from db import Session
from aiogram import types

router = Router()
config = load_config()

# Определение состояний для FSM
class OrderStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_percent = State()
    waiting_for_confirmation = State()

async def start(message: Message):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личном чате с ботом.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить USDT💵", callback_data="start_buy")],
        [InlineKeyboardButton(text="Продать USDT💵", callback_data="start_sell")]
    ])
    await message.answer("Выберите действие:", reply_markup=keyboard)
    await message.delete()

@router.message(Command("sell"))
async def sell_command(message: Message, state: FSMContext):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личном чате с ботом.")
        return
    await start_sell_order(message, state)

@router.message(Command("buy"))
async def buy_command(message: Message, state: FSMContext):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личном чате с ботом.")
        return
    await start_buy_order(message, state)

async def start_sell_order(event: types.Message or CallbackQuery, state: FSMContext):
    await state.update_data(order_type=OrderType.SELL)
    if isinstance(event, Message):
        await event.answer("Введите сумму (в USDT💵):")
    elif isinstance(event, CallbackQuery):
        await event.message.answer("Введите сумму (в USDT💵):")
    await state.set_state(OrderStates.waiting_for_amount)

async def start_buy_order(event: types.Message or CallbackQuery, state: FSMContext):
    await state.update_data(order_type=OrderType.BUY)
    if isinstance(event, Message):
        await event.answer("Введите сумму (в USDT💵):")
    elif isinstance(event, CallbackQuery):
        await event.message.answer("Введите сумму (в USDT💵):")
    await state.set_state(OrderStates.waiting_for_amount)

@router.message(OrderStates.waiting_for_amount)
async def enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        await state.update_data(amount=amount)
        await message.answer("Введите процент:")
        await state.set_state(OrderStates.waiting_for_percent)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")
    await message.delete()

@router.message(OrderStates.waiting_for_percent)
async def enter_percent(message: Message, state: FSMContext):
    try:
        percent = float(message.text)
        await state.update_data(percent=percent)

        user_data = await state.get_data()
        amount = user_data['amount']
        order_type = user_data['order_type']

        order = Order(
            order_type=order_type,
            amount=amount,
            price=0,
            percent=percent,
            creator_username=message.from_user.username,
            creator_user_id=message.from_user.id
        )

        with Session() as session:
            session.add(order)
            session.commit()
            session.refresh(order)

        order_type_text = 'Продажа' if order_type == OrderType.SELL else 'Покупка'
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить ордер", callback_data=f"confirm_{order.id}")],
            [InlineKeyboardButton(text="✏️ Изменить ордер", callback_data=f"edit_{order.id}")],
            [InlineKeyboardButton(text="❌ Удалить ордер", callback_data=f"delete_order_{order.id}")]
        ])

        await message.answer(f"Пожалуйста, подтвердите ваш ордер:\n"
                             f"Тип: {order_type_text}\n"
                             f"Сумма: {amount} USDT💵\nПроцент: {percent}%",
                             reply_markup=keyboard)
        await state.set_state(OrderStates.waiting_for_confirmation)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")
    await message.delete()

@router.message(Command("my_orders"))
async def my_orders(message: Message):
    with Session() as session:
        orders = session.query(Order).filter(Order.creator_user_id == message.from_user.id, Order.is_accepted == False).all()

    if not orders:
        await message.answer("У вас нет активных ордеров, которые можно удалить.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"Удалить ордер #{order.id} ({order.amount} USDT)",
                callback_data=f"delete_order_{order.id}"
            )
        ] for order in orders
    ])

    await message.answer("Ваши активные ордера:", reply_markup=keyboard)

@router.message(Command("admin_orders"))
async def admin_orders(message: Message):
    if message.from_user.id not in config.admin_chat_ids:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    with Session() as session:
        orders = session.query(Order).all()

    if not orders:
        await message.answer("Нет активных ордеров.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for order in orders:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Удалить ордер #{order.id} ({order.amount} USDT)",
                callback_data=f"admin_delete_order_{order.id}"
            )
        ])

    await message.answer("Все активные ордера:", reply_markup=keyboard)


@router.message(Command("orders"))
async def show_all_orders(message: Message):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личном чате с ботом.")
        return

    with Session() as session:
        orders = session.query(Order).all()
        if orders:
            orders_text = "\n\n".join([
                f"Ордер #{order.id}: {'Продажа' if order.order_type == OrderType.SELL else 'Покупка'}\n"
                f"Сумма: {order.amount} USDT💵\nПроцент: {order.percent}%" for order in orders
            ])
            await message.answer(f"Все ордера:\n\n{orders_text}")
        else:
            await message.answer("Нет активных ордеров.")
    await message.delete()

@router.message(Command("clear_orders"))
async def clear_orders(message: Message):
    if message.from_user.id not in config.admin_chat_ids:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    with Session() as session:
        session.query(Order).delete()
        session.commit()

    await message.answer("История ордеров очищена.")
    await message.delete()

def register_handlers(router: Router):
    router.message.register(start, Command(commands=["start"]))
    router.message.register(sell_command, Command(commands=["sell"]))
    router.message.register(buy_command, Command(commands=["buy"]))
    router.callback_query.register(start_sell_order, F.data == "start_sell")
    router.callback_query.register(start_buy_order, F.data == "start_buy")
    router.message.register(my_orders, Command(commands=["my_orders"]))
    router.message.register(enter_amount, OrderStates.waiting_for_amount)
    router.message.register(enter_percent, OrderStates.waiting_for_percent)
    router.message.register(show_all_orders, Command(commands=["orders"]))
    router.message.register(admin_orders, Command(commands=["admin_orders"]))
    router.message.register(clear_orders, Command(commands=["clear_orders"]))
