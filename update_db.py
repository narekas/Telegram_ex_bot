import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('orders.db')  # Убедитесь, что путь к базе данных указан правильно
cursor = conn.cursor()

# Выполнение команды для добавления столбца
try:
    cursor.execute("ALTER TABLE orders ADD COLUMN is_accepted BOOLEAN DEFAULT 0;")
    print("Столбец 'is_accepted' успешно добавлен.")
except sqlite3.OperationalError as e:
    print(f"Ошибка: {e}")

# Сохранение изменений и закрытие соединения
conn.commit()
conn.close()
