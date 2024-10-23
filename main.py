import os
import sqlite3
import valve.source.a2s
import valve.source.master_server
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
from dotenv import load_dotenv
import logging

# Загрузка переменных из .env файла
load_dotenv()

# Получаем токен бота из переменной окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Необходимо установить переменную TELEGRAM_BOT_TOKEN в файле .env")

# Имя файла базы данных SQLite
DB_FILENAME = 'players.db'

# Состояния для ConversationHandler
ADD_PLAYER = 1
DELETE_PLAYER = 2

def init_db():
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (name TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def add_player_to_db(player_name):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO players (name) VALUES (?)', (player_name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Игнорируем, если игрок уже есть в базе
    conn.close()

def get_players_from_db():
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('SELECT name FROM players')
    players = [row[0] for row in c.fetchall()]
    conn.close()
    return players

def remove_player_from_db(player_name):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('DELETE FROM players WHERE name = ?', (player_name,))
    conn.commit()
    conn.close()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['Поиск игроков', 'Добавить игрока'], ['Список игроков', 'Удалить игрока']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Выберите действие:",
        reply_markup=reply_markup
    )

async def list_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_names = get_players_from_db()
    count = len(player_names)
    if count > 0:
        response = f"В списке отслеживается {count} игрок(ов):\n" + '\n'.join(player_names)
    else:
        response = "Список игроков пуст."
    await update.message.reply_text(response)

async def l4d2_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем список игроков из базы данных
    player_names = get_players_from_db()

    if not player_names:
        await update.message.reply_text("Список игроков пуст. Добавьте игроков, нажав кнопку 'Добавить игрока'.")
        return

    # Уведомляем пользователя, что запрос обрабатывается
    await update.message.reply_text("Пожалуйста, подождите, идёт поиск игроков...")

    try:
        servers_with_players = await find_players_on_servers(player_names)
        if servers_with_players:
            response = "Найдены следующие серверы с указанными игроками:\n"
            for server in servers_with_players:
                response += f"\nСервер: {server['server_name']} (CONNECT {server['address']})\n"
                response += f"Игроки: {', '.join(server['players'])}\n"
        else:
            response = "На данный момент указанные игроки не найдены на серверах."
        await update.message.reply_text(response)
    except Exception as e:
        logging.error(f"Произошла ошибка при обработке команды /l4d2: {e}")
        await update.message.reply_text("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
async def add_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, введите имя игрока или несколько имён через запятую для добавления:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADD_PLAYER

async def add_player_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_names_input = update.message.text
    player_names = [name.strip() for name in player_names_input.split(',') if name.strip()]
    if not player_names:
        await update.message.reply_text("Вы не ввели ни одного корректного имени. Попробуйте ещё раз.")
        return ADD_PLAYER

    for player_name in player_names:
        add_player_to_db(player_name)

    keyboard = [['Поиск игроков', 'Добавить игрока'], ['Список игроков', 'Удалить игрока']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"Игроки добавлены: {', '.join(player_names)}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def delete_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_names = get_players_from_db()
    if not player_names:
        await update.message.reply_text("Список игроков пуст. Нечего удалять.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Пожалуйста, введите имя игрока или несколько имён через запятую для удаления:",
        reply_markup=ReplyKeyboardRemove()
    )
    return DELETE_PLAYER

async def delete_player_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_names_input = update.message.text
    player_names_to_remove = [name.strip() for name in player_names_input.split(',') if name.strip()]
    if not player_names_to_remove:
        await update.message.reply_text("Вы не ввели ни одного корректного имени. Попробуйте ещё раз.")
        return DELETE_PLAYER

    existing_players = get_players_from_db()
    removed_players = []
    not_found_players = []

    for player_name in player_names_to_remove:
        if player_name in existing_players:
            remove_player_from_db(player_name)
            removed_players.append(player_name)
        else:
            not_found_players.append(player_name)

    keyboard = [['Поиск игроков', 'Добавить игрока'], ['Список игроков', 'Удалить игрока']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    response = ""
    if removed_players:
        response += f"Игроки удалены: {', '.join(removed_players)}\n"
    if not_found_players:
        response += f"Игроки не найдены в списке: {', '.join(not_found_players)}\n"

    await update.message.reply_text(
        response.strip(),
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['Поиск игроков', 'Добавить игрока'], ['Список игроков', 'Удалить игрока']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def find_players_on_servers(player_names):
    servers_with_players = []
    servers = []
    # Поиск серверов Left 4 Dead 2 с названием, содержащим "zozo.gg" и "BLOOD FACTORY"
    with valve.source.master_server.MasterServerQuerier() as msq:
        for address in msq.find(gamedir='left4dead2', name_match='*zozo.gg*BLOOD FACTORY*'):
            servers.append(address)

    # Получение информации о каждом сервере и списке игроков
    for address in servers:
        try:
            with valve.source.a2s.ServerQuerier(address) as server:
                info = server.info()
                players = server.players()
                # Проверяем, есть ли заданные игроки на сервере
                player_names_on_server = [player['name'] for player in players['players']]
                matching_players = set(player_names) & set(player_names_on_server)
                if matching_players:
                    servers_with_players.append({
                        'address': f"{address[0]}:{address[1]}",
                        'server_name': info['server_name'],
                        'players': matching_players
                    })
        except valve.source.a2s.NoResponseError:
            continue
        except Exception as e:
            logging.error(f"Ошибка при обращении к серверу {address[0]}:{address[1]}: {e}")
            continue
    return servers_with_players

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'Поиск игроков':
        await l4d2_command(update, context)
    elif text == 'Добавить игрока':
        return await add_player_start(update, context)
    elif text == 'Удалить игрока':
        return await delete_player_start(update, context)
    elif text == 'Список игроков':
        await list_players(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выберите действие, используя кнопки.")

def main():
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    # Инициализация базы данных
    init_db()

    # Создание приложения бота
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработчик ConversationHandler для добавления и удаления игрока
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^Добавить игрока$'), add_player_start),
            MessageHandler(filters.Regex('^Удалить игрока$'), delete_player_start)
        ],
        states={
            ADD_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_player_finish)],
            DELETE_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_player_finish)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавление обработчиков команд и сообщений
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('l4d2', l4d2_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()