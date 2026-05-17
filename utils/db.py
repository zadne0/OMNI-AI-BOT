import aiosqlite
import os

DB_PATH = 'data/database.db'

async def init_db():
    # Создаем папку data, если её нет
    if not os.path.exists('data'):
        os.makedirs('data')
        
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица для настроек пользователей (выбранная модель)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                selected_model TEXT DEFAULT 'qwen/qwen-2.5-72b-instruct'
            )
        ''')
        # Таблица для истории (если захочешь сделать память)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT
            )
        ''')
        await db.commit()

async def update_user_model(user_id, model):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO users (user_id, selected_model) 
            VALUES (?, ?) 
            ON CONFLICT(user_id) DO UPDATE SET selected_model = EXCLUDED.selected_model
        ''', (user_id, model))
        await db.commit()

async def get_user_model(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT selected_model FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 'qwen/qwen-2.5-72b-instruct'
async def save_message(user_id, role, content):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)',
            (user_id, role, content)
        )
        # Опционально: удаляем старые сообщения (больше 20), чтобы база не раздувалась
        await db.execute('''
            DELETE FROM history WHERE id IN (
                SELECT id FROM history WHERE user_id = ? 
                ORDER BY id DESC LIMIT -1 OFFSET 20
            )
        ''', (user_id,))
        await db.commit()

async def get_history(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT role, content FROM history WHERE user_id = ? ORDER BY id ASC',
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"role": r, "content": c} for r, c in rows]
