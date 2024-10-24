# server_query.py
import valve.source.a2s
import logging
from db import get_servers_from_db

async def find_players_on_servers(player_names):
    servers_with_players = []
    server_addresses = get_servers_from_db()

    if not server_addresses:
        return servers_with_players

    # Преобразуем адреса в формат (ip, port)
    servers = []
    for address in server_addresses:
        ip_port = address.split(':')
        if len(ip_port) == 2:
            servers.append((ip_port[0], int(ip_port[1])))
        else:
            logging.error(f"Неверный формат адреса сервера: {address}")

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
            logging.warning(f"Нет ответа от сервера {address[0]}:{address[1]}")
            continue
        except Exception as e:
            logging.error(f"Ошибка при обращении к серверу {address[0]}:{address[1]}: {e}")
            continue
    return servers_with_players