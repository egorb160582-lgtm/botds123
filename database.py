import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

DATABASE_PATH = "data/bot_database.db"


def get_connection():
    """Создает подключение к базе данных."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Инициализирует базу данных и создает таблицы."""
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица настроек гильдии
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            clan_name TEXT DEFAULT 'Клан',
            panel_image_url TEXT,
            panel_text TEXT,
            applications_category_id INTEGER,
            branch_channel_id INTEGER,
            member_role_id INTEGER,
            welcome_role_id INTEGER,
            welcome_image_url TEXT,
            moderator_roles TEXT DEFAULT '[]',
            moderator_users TEXT DEFAULT '[]',
            logs_channel_id INTEGER
        )
    """)

    # Миграция: добавляем колонку logs_channel_id если её нет
    try:
        cursor.execute("ALTER TABLE guild_settings ADD COLUMN logs_channel_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Колонка уже существует

    # Таблица заявок
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            user_id INTEGER,
            username TEXT,
            static TEXT,
            hours_per_day TEXT,
            age_oos TEXT,
            ready_online TEXT,
            how_found TEXT,
            status TEXT DEFAULT 'pending',
            message_id INTEGER,
            channel_id INTEGER,
            member_thread_id INTEGER,
            moderator_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ==================== Guild Settings ====================

def get_guild_settings(guild_id: int) -> Optional[Dict[str, Any]]:
    """Получает настройки гильдии."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        data = dict(row)
        data['moderator_roles'] = json.loads(data['moderator_roles']) if data.get('moderator_roles') else []
        data['moderator_users'] = json.loads(data['moderator_users']) if data.get('moderator_users') else []
        return data
    return None


def save_guild_settings(guild_id: int, **kwargs) -> None:
    """Сохраняет настройки гильдии."""
    conn = get_connection()
    cursor = conn.cursor()

    # Преобразуем списки в JSON
    for key in ['moderator_roles', 'moderator_users']:
        if key in kwargs and isinstance(kwargs[key], list):
            kwargs[key] = json.dumps(kwargs[key])

    existing = get_guild_settings(guild_id)

    if existing:
        # Update
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [guild_id]
        cursor.execute(f"UPDATE guild_settings SET {set_clause} WHERE guild_id = ?", values)
    else:
        # Insert
        kwargs['guild_id'] = guild_id
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?" for _ in kwargs])
        cursor.execute(f"INSERT INTO guild_settings ({columns}) VALUES ({placeholders})", list(kwargs.values()))

    conn.commit()
    conn.close()


# ==================== Applications ====================

def create_application(
    guild_id: int,
    user_id: int,
    username: str,
    static: str,
    hours_per_day: str,
    age_oos: str,
    ready_online: str,
    how_found: Optional[str] = None
) -> int:
    """Создает новую заявку и возвращает её ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications
        (guild_id, user_id, username, static, hours_per_day, age_oos, ready_online, how_found)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (guild_id, user_id, username, static, hours_per_day, age_oos, ready_online, how_found))

    application_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return application_id


def get_application(application_id: int) -> Optional[Dict[str, Any]]:
    """Получает заявку по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE id = ?", (application_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_application_by_message(message_id: int) -> Optional[Dict[str, Any]]:
    """Получает заявку по ID сообщения."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_application_by_channel(channel_id: int) -> Optional[Dict[str, Any]]:
    """Получает заявку по ID канала."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE channel_id = ?", (channel_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_application(application_id: int, **kwargs) -> None:
    """Обновляет заявку."""
    conn = get_connection()
    cursor = conn.cursor()

    kwargs['updated_at'] = datetime.now().isoformat()
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [application_id]

    cursor.execute(f"UPDATE applications SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_pending_application(guild_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Проверяет, есть ли у пользователя активная заявка."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM applications
        WHERE guild_id = ? AND user_id = ? AND status IN ('pending', 'reviewing')
        ORDER BY created_at DESC
        LIMIT 1
    """, (guild_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_member_threads(guild_id: int, user_id: int) -> List[Dict[str, Any]]:
    """Получает все ветки участника для пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM applications
        WHERE guild_id = ? AND user_id = ? AND member_thread_id IS NOT NULL AND status = 'accepted'
    """, (guild_id, user_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Инициализация при импорте
init_database()
