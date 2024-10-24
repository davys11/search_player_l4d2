# main.py
import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler
)
from constants import TELEGRAM_BOT_TOKEN, ADD_PLAYER, DELETE_PLAYER, ADD_SERVER, DELETE_SERVER
from db import init_db
from handlers import (
    start_command, l4d2_command, list_players, handle_text, error_handler,
    add_player_start, add_player_finish, delete_player_start, delete_player_finish, cancel,
    add_server_start, add_server_finish, delete_server_start, delete_server_finish, list_servers
)

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

    # Обработчик ConversationHandler для добавления и удаления игроков и серверов
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^Добавить игрока$'), add_player_start),
            MessageHandler(filters.Regex('^Удалить игрока$'), delete_player_start),
            MessageHandler(filters.Regex('^Добавить сервер$'), add_server_start),
            MessageHandler(filters.Regex('^Удалить сервер$'), delete_server_start)
        ],
        states={
            ADD_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_player_finish)],
            DELETE_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_player_finish)],
            ADD_SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_server_finish)],
            DELETE_SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_server_finish)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавление обработчиков команд и сообщений
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('l4d2', l4d2_command))
    application.add_handler(CommandHandler('list_players', list_players))
    application.add_handler(CommandHandler('list_servers', list_servers))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Обработка ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()