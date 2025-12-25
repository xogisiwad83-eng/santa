import sqlite3
import random
import string
from config import config
from typing import Optional, Dict, List


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
    
    def get_game_by_code(self, code: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM games WHERE code = ?", (code,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    def add_participant(self, game_code: str, user_id: int, user_name: str, wishes: str = "") -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        game = self.get_game_by_code(game_code)
        if not game or game["is_drawn"]:
            conn.close()
            return False
        
        try:
            cursor.execute("""
                INSERT INTO participants (game_id, user_id, user_name, wishes, joined_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (game["id"], user_id, user_name, wishes))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_participants(self, game_code: str) -> List[Dict]:
        game = self.get_game_by_code(game_code)
        if not game:
            return []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM participants 
            WHERE game_id = ? 
            ORDER BY joined_at
        """, (game["id"],))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            dict(r)
            for r in rows
        ]
        
    def get_user_game(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT *
                       FROM games
                       WHERE creator_id = ? AND is_drawn = 0
                       ORDER BY created_at DESC 
                       LIMIT 1
                       """, (user_id,))
        game = cursor.fetchone()
        if game:
            conn.close()
            return dict(game)
        cursor.execute("""
                       SELECT g.*
                       FROM games g
                       JOIN participants p
                       ON g.id = p.game_id
                       WHERE p.user_id = ?
                       ORDER BY p.joined_at DESC 
                       LIMIT 1
                       """, (user_id,))
        game = cursor.fetchone()
        conn.close()
        if game:
            return dict(game)
        return None    
    
    def perform_draw(self, game_code: str) -> bool:
        game = self.get_game_by_code(game_code)
        if not game:
            return False
        if game['is_drawn']:
            return False
        
        participants = self.get_participants(game_code)
        if len(participants) < 3:
            return False
        
        givers = [p['id'] for p in participants]
        
        receivers = givers.copy()
        
        max_attempts = 100
        for _ in range(max_attempts):
            random.shuffle(receivers)
            
            # Проверяем, что никто не дарит сам себе
            if all(g != r for g, r in zip(givers, receivers)):
                break
        else:
            # Если не удалось после 100 попыток, используем алгоритм сдвига
            receivers = givers[1:] + [givers[0]]
        conn = self.get_connection()
        cursor = conn.cursor()
        
        
        for giver_id, receiver_id in zip(givers, receivers):
            cursor.execute("""
                INSERT INTO assignments (game_id, giver_id, receiver_id)
                VALUES (?, ?, ?)
            """, (game['id'], giver_id, receiver_id))
            
        cursor.execute("""
            UPDATE games SET is_drawn = 1
            WHERE id = ?
        """, (game['id'],))
        
        conn.commit()
        conn.close()
        
        return True
            

 
db = Database(config.DATABASE_PATH)