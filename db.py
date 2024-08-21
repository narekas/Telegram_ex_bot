from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import load_config

# Загрузка конфигурации
config = load_config()

# Создаем движок для работы с базой данных
engine = create_engine(config.database_url)

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем фабрику сессий
Session = sessionmaker(bind=engine)


def init_db():
    # Импортируем все модели, чтобы они были зарегистрированы в метаданных Base
    import models.order  # Замените на ваш файл с моделями

    # Создаем все таблицы в базе данных
    Base.metadata.create_all(engine)
