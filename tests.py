import unittest
from app import app
from database_manager import DatabaseManager
import psycopg2
import json

class TestPerevalAPI(unittest.TestCase):
    def setUp(self):
        # Настройка тестовой базы данных
        self.db = DatabaseManager()
        self.db.conn_params['dbname'] = 'pereval_test'  # Используем тестовую БД
        self.db.connect()
        self.db.cursor.execute("TRUNCATE TABLE pass_images, pereval_images, pereval_added, users, coords, levels RESTART IDENTITY;")
        self.db.conn.commit()

        # Настройка тестового клиента Flask
        self.app = app.test_client()
        self.app.testing = True

        # Тестовые данные
        self.test_data = {
            "beauty_title": "пер. ",
            "title": "Пхия",
            "other_titles": "Триев",
            "connect": "",
            "add_time": "2021-09-22 13:18:13",
            "user": {
                "email": "test@example.com",
                "fam": "Пупкин",
                "name": "Василий",
                "otc": "Иванович",
                "phone": "+7 555 55 55"
            },
            "coords": {
                "latitude": "45.3842",
                "longitude": "7.1525",
                "height": "1200"
            },
            "level": {
                "winter": "",
                "summer": "1А",
                "autumn": "1А",
                "spring": ""
            },
            "images": [
                {"data": "test_image_1", "title": "Седловина"},
                {"data": "test_image_2", "title": "Подъём"}
            ]
        }

    def tearDown(self):
        # Очистка тестовой базы данных
        self.db.cursor.execute("TRUNCATE TABLE pass_images, pereval_images, pereval_added, users, coords, levels RESTART IDENTITY;")
        self.db.conn.commit()
        self.db.close()

    def test_submit_data(self):
        """Тест добавления нового перевала"""
        result = self.db.submit_data(self.test_data)
        self.assertEqual(result['status'], 200)
        self.assertEqual(result['message'], "Отправлено успешно")
        self.assertIsNotNone(result['id'])

    def test_submit_and_get_pass(self):
        """Тест добавления и получения перевала по ID"""
        # Добавление перевала
        submit_result = self.db.submit_data(self.test_data)
        pass_id = submit_result['id']
        self.assertEqual(submit_result['status'], 200)

        # Получение перевала
        get_result = self.db.get_pass_by_id(pass_id)
        self.assertEqual(get_result['status'], 200)
        self.assertEqual(get_result['data']['title'], self.test_data['title'])
        self.assertEqual(get_result['data']['user']['email'], self.test_data['user']['email'])
        self.assertEqual(len(get_result['data']['images']), 2)

    def test_update_pass(self):
        """Тест редактирования перевала"""
        # Добавление перевала
        submit_result = self.db.submit_data(self.test_data)
        pass_id = submit_result['id']

        # Обновление данных
        updated_data = self.test_data.copy()
        updated_data['title'] = "Пхия Updated"
        updated_data['coords']['height'] = "1300"
        update_result = self.db.update_pass(pass_id, updated_data)
        self.assertEqual(update_result['state'], 1)
        self.assertEqual(update_result['message'], "Запись успешно обновлена")

        # Проверка обновлённых данных
        get_result = self.db.get_pass_by_id(pass_id)
        self.assertEqual(get_result['data']['title'], "Пхия Updated")
        self.assertEqual(get_result['data']['coords']['height'], 1300)

    def test_update_pass_not_new(self):
        """Тест редактирования перевала с неподходящим статусом"""
        # Добавление перевала
        submit_result = self.db.submit_data(self.test_data)
        pass_id = submit_result['id']

        # Изменение статуса на 'pending'
        self.db.cursor.execute("UPDATE pereval_added SET status = 'pending' WHERE id = %s;", (pass_id,))
        self.db.conn.commit()

        # Попытка редактирования
        update_result = self.db.update_pass(pass_id, self.test_data)
        self.assertEqual(update_result['state'], 0)
        self.assertEqual(update_result['message'], "Редактирование запрещено: статус не 'new'")

    def test_get_passes_by_email(self):
        """Тест получения списка перевалов по email"""
        # Добавление двух перевалов
        self.db.submit_data(self.test_data)
        second_data = self.test_data.copy()
        second_data['title'] = "Пхия 2"
        self.db.submit_data(second_data)

        # Получение списка перевалов
        result = self.db.get_passes_by_user_email("test@example.com")
        self.assertEqual(result['status'], 200)
        self.assertEqual(len(result['data']), 2)
        self.assertEqual(result['data'][0]['user']['email'], "test@example.com")

    def test_api_submit_data(self):
        """Тест API: добавление перевала"""
        response = self.app.post('/submitData', json=self.test_data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 200)
        self.assertEqual(data['message'], "Отправлено успешно")

    def test_api_get_pass(self):
        """Тест API: получение перевала по ID"""
        submit_result = self.db.submit_data(self.test_data)
        pass_id = submit_result['id']
        response = self.app.get(f'/submitData/{pass_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 200)
        self.assertEqual(data['data']['title'], self.test_data['title'])

    def test_api_update_pass(self):
        """Тест API: обновление перевала"""
        submit_result = self.db.submit_data(self.test_data)
        pass_id = submit_result['id']
        updated_data = self.test_data.copy()
        updated_data['title'] = "Пхия Updated"
        response = self.app.patch(f'/submitData/{pass_id}', json=updated_data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['state'], 1)

    def test_api_get_passes_by_email(self):
        """Тест API: получение перевалов по email"""
        self.db.submit_data(self.test_data)
        response = self.app.get('/submitData/?user__email=test@example.com')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 200)
        self.assertEqual(len(data['data']), 1)

if __name__ == '__main__':
    unittest.main()