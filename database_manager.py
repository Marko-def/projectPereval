import os
import psycopg2
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('FSTR_DB_HOST', 'localhost'),
            'port': os.getenv('FSTR_DB_PORT', '5432'),
            'dbname': 'fstr',
            'user': os.getenv('FSTR_DB_LOGIN', 'postgres'),
            'password': os.getenv('FSTR_DB_PASS', 'password')
        }
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return False

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def submit_data(self, data):
        try:
            if not self.connect():
                return {"status": 500, "message": "Ошибка подключения к базе данных", "id": None}

            # Проверка обязательных полей
            required_fields = ['beauty_title', 'title', 'add_time', 'user', 'coords', 'level', 'images']
            for field in required_fields:
                if field not in data:
                    self.close()
                    return {"status": 400, "message": f"Отсутствует поле: {field}", "id": None}

            # Вставка пользователя
            user = data['user']
            self.cursor.execute("""
                INSERT INTO users (email, fam, name, otc, phone)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    fam = EXCLUDED.fam,
                    name = EXCLUDED.name,
                    otc = EXCLUDED.otc,
                    phone = EXCLUDED.phone
                RETURNING id;
            """, (user['email'], user['fam'], user['name'], user.get('otc', ''), user['phone']))
            user_id = self.cursor.fetchone()[0]

            # Вставка координат
            coords = data['coords']
            self.cursor.execute("""
                INSERT INTO coords (latitude, longitude, height)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (coords['latitude'], coords['longitude'], coords['height']))
            coord_id = self.cursor.fetchone()[0]

            # Вставка уровня сложности
            level = data['level']
            self.cursor.execute("""
                INSERT INTO levels (winter, summer, autumn, spring)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (level['winter'], level['summer'], level['autumn'], level['spring']))
            level_id = self.cursor.fetchone()[0]

            # Вставка перевала
            self.cursor.execute("""
                INSERT INTO passes (beauty_title, title, other_titles, connect, add_time, user_id, coord_id, level_id, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'new')
                RETURNING id;
            """, (
                data['beauty_title'],
                data['title'],
                data.get('other_titles', ''),
                data.get('connect', ''),
                datetime.strptime(data['add_time'], '%Y-%m-%d %H:%M:%S'),
                user_id,
                coord_id,
                level_id
            ))
            pass_id = self.cursor.fetchone()[0]

            # Вставка изображений
            for image in data['images']:
                self.cursor.execute("""
                    INSERT INTO images (data, title)
                    VALUES (%s, %s)
                    RETURNING id;
                """, (image['data'], image['title']))
                image_id = self.cursor.fetchone()[0]

                # Связываем изображение с перевалом
                self.cursor.execute("""
                    INSERT INTO pass_images (pass_id, image_id)
                    VALUES (%s, %s);
                """, (pass_id, image_id))

            self.conn.commit()
            self.close()
            return {"status": 200, "message": "Отправлено успешно", "id": pass_id}

        except Exception as e:
            self.conn.rollback()
            self.close()
            return {"status": 500, "message": f"Ошибка: {str(e)}", "id": None}