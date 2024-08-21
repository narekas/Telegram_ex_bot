from sqlalchemy import Column,Boolean, Integer, String, Float, Enum as SQLAEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum
from db import Base


class OrderType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_type = Column(SQLAEnum(OrderType), nullable=False)  # Используем Enum из SQLAlchemy
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # Если фиат не используется, можно сделать nullable
    percent = Column(Float, nullable=False)
    creator_username = Column(String, nullable=False)
    creator_user_id = Column(Integer, nullable=False)
    is_accepted = Column(Boolean, default=False)
