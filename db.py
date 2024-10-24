# db.py
import sqlite3
from constants import DB_FILENAME

def init_db():
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (name TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS servers (address TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

# Функции для управления игроками
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

# Функции для управления серверами
def add_server_to_db(server_address):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO servers (address) VALUES (?)', (server_address,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Игнорируем, если сервер уже есть в базе
    conn.close()

def get_servers_from_db():
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('SELECT address FROM servers')
    servers = [row[0] for row in c.fetchall()]
    conn.close()
    return servers

def remove_server_from_db(server_address):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('DELETE FROM servers WHERE address = ?', (server_address,))
    conn.commit()
    conn.close()