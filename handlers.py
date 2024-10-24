# handlers.py
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import logging
from constants import (
    KEYBOARD_MAIN, ADD_PLAYER, DELETE_PLAYER, ADD_SERVER, DELETE_SERVER
)
from db import (
    add_player_to_db, get_players_from_db, remove_player_from_db,
    add_server_to_db, get_servers_from_db, remove_server_from_db
)
from server_query import find_players_on_servers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True)
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
    player_names = get_players_from_db()
    if not player_names:
        await update.message.reply_text("Список игроков пуст. Добавьте игроков, нажав кнопку 'Добавить игрока'.")
        return

    server_addresses = get_servers_from_db()
    if not server_addresses:
        await update.message.reply_text("Список серверов пуст. Добавьте серверы, нажав кнопку 'Добавить сервер'.")
        return

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

    reply_markup = ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True)

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

    reply_markup = ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True)

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

async def list_servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server_addresses = get_servers_from_db()
    count = len(server_addresses)
    if count > 0:
        response = f"В списке отслеживается {count} сервер(ов):\n" + '\n'.join(server_addresses)
    else:
        response = "Список серверов пуст."
    await update.message.reply_text(response)

async def add_server_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, введите адрес сервера или несколько адресов через запятую для добавления (формат IP:PORT):",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADD_SERVER

async def add_server_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server_addresses_input = update.message.text
    server_addresses = [addr.strip() for addr in server_addresses_input.split(',') if addr.strip()]
    if not server_addresses:
        await update.message.reply_text("Вы не ввели ни одного корректного адреса. Попробуйте ещё раз.")
        return ADD_SERVER

    for server_address in server_addresses:
        add_server_to_db(server_address)

    reply_markup = ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True)

    await update.message.reply_text(
        f"Сервера добавлены: {', '.join(server_addresses)}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def delete_server_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server_addresses = get_servers_from_db()
    if not server_addresses:
        await update.message.reply_text("Список серверов пуст. Нечего удалять.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Пожалуйста, введите адрес сервера или несколько адресов через запятую для удаления (формат IP:PORT):",
        reply_markup=ReplyKeyboardRemove()
    )
    return DELETE_SERVER

async def delete_server_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server_addresses_input = update.message.text
    server_addresses_to_remove = [addr.strip() for addr in server_addresses_input.split(',') if addr.strip()]
    if not server_addresses_to_remove:
        await update.message.reply_text("Вы не ввели ни одного корректного адреса. Попробуйте ещё раз.")
        return DELETE_SERVER

    existing_servers = get_servers_from_db()
    removed_servers = []
    not_found_servers = []

    for server_address in server_addresses_to_remove:
        if server_address in existing_servers:
            remove_server_from_db(server_address)
            removed_servers.append(server_address)
        else:
            not_found_servers.append(server_address)

    reply_markup = ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True)

    response = ""
    if removed_servers:
        response += f"Сервера удалены: {', '.join(removed_servers)}\n"
    if not_found_servers:
        response += f"Сервера не найдены в списке: {', '.join(not_found_servers)}\n"

    await update.message.reply_text(
        response.strip(),
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True)
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

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
    elif text == 'Добавить сервер':
        return await add_server_start(update, context)
    elif text == 'Удалить сервер':
        return await delete_server_start(update, context)
    elif text == 'Список серверов':
        await list_servers(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выберите действие, используя кнопки.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)