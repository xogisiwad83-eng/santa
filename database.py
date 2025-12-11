import sqlite3
import random
import string
from config import config


class Database:
    """Класс для работы с базой данных"""

    def __init__(self, db_path: str):
        """Инициализация подключения к БД"""
        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Получение подключения к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Доступ к полям по имени
        return conn

    def init_database(self):
        """Инициализация БД - создание таблиц"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица игр
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                creator_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_drawn BOOLEAN DEFAULT 0
            )
        """)

        # Таблица участников
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                wishes TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games (id),
                UNIQUE(game_id, user_id)
            )
        """)

        # Таблица распределения
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                giver_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                FOREIGN KEY (game_id) REFERENCES games (id),
                FOREIGN KEY (giver_id) REFERENCES participants (id),
                FOREIGN KEY (receiver_id) REFERENCES participants (id),
                UNIQUE(game_id, giver_id)
            )
        """)

        conn.commit()
        conn.close()

    def generate_game_code(self) -> str:
        """Генерация уникального 6-значного кода игры"""
        while True:
            code = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=6
            ))

            # Проверяем уникальность
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM games WHERE code = ?", (code,))
            exists = cursor.fetchone()
            conn.close()

            if not exists:
                return code

    def create_game(self, creator_id: int) -> str:
        """
        Создание новой игры
        
        Args:
            creator_id: Telegram ID создателя
            
        Returns:
            Код игры
        """
        code = self.generate_game_code()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
                       select id from games
                       where creator_id = ? and is_drawn = 0
                    """, (creator_id,))
        existing_game = cursor.fetchone()
        if existing_game:
            game_id = existing_game['id']
            cursor.execute('delete from games where id = ?', (game_id,)) 
            cursor.execute('delete from assignments where game_id = ?', (game_id,))
            cursor.execute('delete from participants where game_id = ?', (game_id,)) 
        
        cursor.execute("""
                       insert into games (code, creator_id)
                       values (?,?)
                       """, (code, creator_id))
        
        conn.commit()
        conn.close()
        return code   

 
db = Database(config.DATABASE_PATH)