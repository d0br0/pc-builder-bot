import sqlite3
from contextlib import contextmanager

class BuildSaver:
    def __init__(self, db_path='bot_data.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_builds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    cpu TEXT,
                    gpu TEXT,
                    motherboard TEXT,
                    ram TEXT,
                    ssd TEXT,
                    psu TEXT,
                    pc_case TEXT,
                    cooler TEXT,
                    total_price INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    @contextmanager
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def save_build(self, user_id, build_data):
        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO user_builds (user_id, cpu, gpu, motherboard, ram, ssd, psu, pc_case, cooler, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                build_data['cpu']['name'] if build_data['cpu'] else None,
                build_data['gpu']['name'] if build_data['gpu'] else None,
                build_data['motherboard']['name'] if build_data['motherboard'] else None,
                build_data['ram']['name'] if build_data['ram'] else None,
                build_data['ssd']['name'] if build_data['ssd'] else None,
                build_data['psu']['name'] if build_data['psu'] else None,
                build_data['pc_case']['name'] if build_data['pc_case'] else None,
                build_data['cooler']['name'] if build_data['cooler'] else None,
                build_data['total_price']
            ))

            cursor.execute('''
                DELETE FROM user_builds
                WHERE user_id = ?
                AND id NOT IN (
                    SELECT id FROM user_builds
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 10
                );
            ''', (user_id, user_id))

            conn.commit()

    def get_builds_by_user_id(self, user_id):
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, cpu, gpu, motherboard, ram, ssd, psu, pc_case, cooler, total_price, created_at
                FROM user_builds
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            return [
                {
                    'id': r[0],
                    'cpu': r[1],
                    'gpu': r[2],
                    'motherboard': r[3],
                    'ram': r[4],
                    'ssd': r[5],
                    'psu': r[6],
                    'pc_case': r[7],
                    'cooler': r[8],
                    'total_price': r[9],
                    'created_at': r[10]
                }
                for r in rows
            ]
        
    def get_build_by_id(self, build_id):
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cpu, gpu, motherboard, ram, ssd, psu, pc_case, cooler, total_price, created_at
                FROM user_builds
                WHERE id = ?
            ''', (build_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'cpu': row[0],
                    'gpu': row[1],
                    'motherboard': row[2],
                    'ram': row[3],
                    'ssd': row[4],
                    'psu': row[5],
                    'pc_case': row[6],
                    'cooler': row[7],
                    'total_price': row[8],
                    'created_at': row[9]
                }
            return None