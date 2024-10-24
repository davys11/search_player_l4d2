# constants.py
import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Получаем токен бота из переменной окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Необходимо установить переменную TELEGRAM_BOT_TOKEN в файле .env")

# Имя файла базы данных SQLite
DB_FILENAME = 'players.db'

# Клавиатура для основного меню
KEYBOARD_MAIN = [
    ['Поиск игроков', 'Добавить игрока'],
    ['Список игроков', 'Удалить игрока'],
    ['Добавить сервер', 'Удалить сервер'],
    ['Список серверов']
]

# Состояния для ConversationHandler
ADD_PLAYER = 1
DELETE_PLAYER = 2
ADD_SERVER = 3
DELETE_SERVER = 4