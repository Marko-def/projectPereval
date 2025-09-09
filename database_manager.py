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

    def get_pass_by_id(self, pass_id):
        try:
            if not self.connect():
                return {"status": 500, "message": "Ошибка подключения к базе данных", "data": None}

            # Запрос данных о перевале
            self.cursor.execute("""
                SELECT pa.id, pa.beauty_title, pa.title, pa.other_titles, pa.connect, pa.add_time, pa.status,
                       u.id as user_id, u.email, u.fam, u.name, u.otc, u.phone,
                       c.latitude, c.longitude, c.height,
                       l.winter, l.summer, l.autumn, l.spring,
                       pa.area_id
                FROM pereval_added pa
                JOIN users u ON pa.user_id = u.id
                JOIN coords c ON pa.coord_id = c.id
                JOIN levels l ON pa.level_id = l.id
                WHERE pa.id = %s;
            """, (pass_id,))
            pass_data = self.cursor.fetchone()

            if not pass_data:
                self.close()
                return {"status": 404, "message": "Перевал не найден", "data": None}

            # Получение изображений
            self.cursor.execute("""
                SELECT pi.id, pi.title, pi.img
                FROM pereval_images pi
                JOIN pass_images ppi ON pi.id = ppi.image_id
                WHERE ppi.pass_id = %s;
            """, (pass_id,))
            images = self.cursor.fetchall()

            # Формирование ответа
            result = {
                "id": pass_data[0],
                "beauty_title": pass_data[1],
                "title": pass_data[2],
                "other_titles": pass_data[3],
                "connect": pass_data[4],
                "add_time": pass_data[5].strftime('%Y-%m-%d %H:%M:%S'),
                "status": pass_data[6],
                "user": {
                    "id": pass_data[7],
                    "email": pass_data[8],
                    "fam": pass_data[9],
                    "name": pass_data[10],
                    "otc": pass_data[11],
                    "phone": pass_data[12]
                },
                "coords": {
                    "latitude": float(pass_data[13]),
                    "longitude": float(pass_data[14]),
                    "height": pass_data[15]
                },
                "level": {
                    "winter": pass_data[16],
                    "summer": pass_data[17],
                    "autumn": pass_data[18],
                    "spring": pass_data[19]
                },
                "images": [{"id": img[0], "title": img[1], "data": img[2]} for img in images],
                "area_id": pass_data[20]
            }

            self.close()
            return {"status": 200, "message": "Успех", "data": result}

        except Exception as e:
            self.close()
            return {"status": 500, "message": f"Ошибка: {str(e)}", "data": None}

    def update_pass(self, pass_id, data):
        try:
            if not self.connect():
                return {"state": 0, "message": "Ошибка подключения к базе данных"}

            # Проверка статуса перевала
            self.cursor.execute("SELECT status FROM pereval_added WHERE id = %s;", (pass_id,))
            pass_status = self.cursor.fetchone()

            if not pass_status:
                self.close()
                return {"state": 0, "message": "Перевал не найден"}

            if pass_status[0] != 'new':
                self.close()
                return {"state": 0, "message": "Редактирование запрещено: статус не 'new'"}

            # Проверка обязательных полей
            required_fields = ['beauty_title', 'title', 'add_time', 'coords', 'level', 'images']
            for field in required_fields:
                if field not in data:
                    self.close()
                    return {"state": 0, "message": f"Отсутствует поле: {field}"}

            # Получение текущего user_id
            self.cursor.execute("SELECT user_id FROM pereval_added WHERE id = %s;", (pass_id,))
            user_id = self.cursor.fetchone()[0]

            # Вставка новых координат
            coords = data['coords']
            self.cursor.execute("""
                INSERT INTO coords (latitude, longitude, height)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (float(coords['latitude']), float(coords['longitude']), int(coords['height'])))
            new_coord_id = self.cursor.fetchone()[0]

            # Вставка нового уровня сложности
            level = data['level']
            self.cursor.execute("""
                INSERT INTO levels (winter, summer, autumn, spring)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (level['winter'], level['summer'], level['autumn'], level['spring']))
            new_level_id = self.cursor.fetchone()[0]

            # Обновление перевала (без изменения user_id)
            self.cursor.execute("""
                UPDATE pereval_added
                SET beauty_title = %s, title = %s, other_titles = %s, connect = %s, 
                    add_time = %s, coord_id = %s, level_id = %s, area_id = %s
                WHERE id = %s;
            """, (
                data['beauty_title'],
                data['title'],
                data.get('other_titles', ''),
                data.get('connect', ''),
                datetime.strptime(data['add_time'], '%Y-%m-%d %H:%M:%S'),
                new_coord_id,
                new_level_id,
                data.get('area_id'),
                pass_id
            ))

            # Удаление старых изображений
            self.cursor.execute("DELETE FROM pass_images WHERE pass_id = %s;", (pass_id,))

            # Вставка новых изображений
            for image in data['images']:
                self.cursor.execute("""
                    INSERT INTO pereval_images (img, title)
                    VALUES (%s, %s)
                    RETURNING id;
                """, (image['data'], image['title']))
                image_id = self.cursor.fetchone()[0]

                self.cursor.execute("""
                    INSERT INTO pass_images (pass_id, image_id)
                    VALUES (%s, %s);
                """, (pass_id, image_id))

            self.conn.commit()
            self.close()
            return {"state": 1, "message": "Запись успешно обновлена"}

        except Exception as e:
            self.conn.rollback()
            self.close()
            return {"state": 0, "message": f"Ошибка: {str(e)}"}

    def get_passes_by_user_email(self, email):
        try:
            if not self.connect():
                return {"status": 500, "message": "Ошибка подключения к базе данных", "data": None}

            # Проверка существования пользователя
            self.cursor.execute("SELECT id FROM users WHERE email = %s;", (email,))
            user = self.cursor.fetchone()
            if not user:
                self.close()
                return {"status": 404, "message": "Пользователь не найден", "data": None}

            user_id = user[0]

            # Получение списка перевалов
            self.cursor.execute("""
                SELECT pa.id, pa.beauty_title, pa.title, pa.other_titles, pa.connect, pa.add_time, pa.status,
                       c.latitude, c.longitude, c.height,
                       l.winter, l.summer, l.autumn, l.spring,
                       pa.area_id
                FROM pereval_added pa
                JOIN users u ON pa.user_id = u.id
                JOIN coords c ON pa.coord_id = c.id
                JOIN levels l ON pa.level_id = l.id
                WHERE u.id = %s;
            """, (user_id,))
            passes = self.cursor.fetchall()

            # Формирование списка результатов
            result = []
            for pass_data in passes:
                pass_id = pass_data[0]
                # Получение изображений для каждого перевала
                self.cursor.execute("""
                    SELECT pi.id, pi.title, pi.img
                    FROM pereval_images pi
                    JOIN pass_images ppi ON pi.id = ppi.image_id
                    WHERE ppi.pass_id = %s;
                """, (pass_id,))
                images = self.cursor.fetchall()

                pass_info = {
                    "id": pass_data[0],
                    "beauty_title": pass_data[1],
                    "title": pass_data[2],
                    "other_titles": pass_data[3],
                    "connect": pass_data[4],
                    "add_time": pass_data[5].strftime('%Y-%m-%d %H:%M:%S'),
                    "status": pass_data[6],
                    "coords": {
                        "latitude": float(pass_data[7]),
                        "longitude": float(pass_data[8]),
                        "height": pass_data[9]
                    },
                    "level": {
                        "winter": pass_data[10],
                        "summer": pass_data[11],
                        "autumn": pass_data[12],
                        "spring": pass_data[13]
                    },
                    "images": [{"id": img[0], "title": img[1], "data": img[2]} for img in images],
                    "area_id": pass_data[14]
                }
                result.append(pass_info)

            self.close()
            return {"status": 200, "message": "Успех", "data": result}

        except Exception as e:
            self.close()
            return {"status": 500, "message": f"Ошибка: {str(e)}", "data": None}