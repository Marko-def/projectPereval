# Перевал: REST API для управления данными о горных перевалах

## Описание проекта

Проект представляет собой REST API для работы с данными о горных перевалах, созданное для Федерации спортивного туризма России (ФСТР). API позволяет туристам добавлять информацию о перевалах, включая координаты, фотографии, уровень сложности и данные пользователя, а также получать и редактировать эти данные. Проект разработан для поддержки мобильного приложения, которое отправляет данные о перевалах для последующей модерации.

### Задача
Создать REST API с методами для:
- Добавления новых данных о перевале (`POST /submitData`).
- Получения данных о перевале по ID (`GET /submitData/<id>`).
- Редактирования существующего перевала, если он в статусе `new` (`PATCH /submitData/<id>`).
- Получения списка перевалов по email пользователя (`GET /submitData/?user__email=<email>`).

API взаимодействует с базой данных PostgreSQL, где данные хранятся в нормализованном виде (таблицы для пользователей, координат, уровней сложности, перевалов и изображений). Проект включает класс для работы с базой данных, обработку ошибок и поддержку переменных окружения для конфигурации.

### Реализованные функции
- **Добавление перевала**: Принимает JSON с данными о перевале, пользователе, координатах, уровне сложности и изображениях. Сохраняет данные в базу и возвращает ID записи.
- **Получение данных о перевале**: Возвращает полную информацию о перевале по его ID, включая статус модерации.
- **Редактирование перевала**: Позволяет обновлять данные перевала (кроме пользовательских данных), если статус записи — `new`.
- **Получение перевалов по email**: Возвращает список всех перевалов, добавленных пользователем с указанным email.
- **Нормализованная база данных**: Данные разделены на таблицы `users`, `coords`, `levels`, `pereval_added`, `pereval_images` и `pass_images` для эффективного хранения и управления.
- **Поддержка переменных окружения**: Конфигурация базы данных (хост, порт, логин, пароль) задаётся через переменные окружения (`FSTR_DB_HOST`, `FSTR_DB_PORT`, `FSTR_DB_LOGIN`, `FSTR_DB_PASS`).

## Установка и запуск

### Требования
- Python 3.8+
- PostgreSQL
- Библиотеки: `flask`, `psycopg2-binary`

### Установка
1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd pereval-api

#Улудшение структуры базы данных

-- Создание базы данных
CREATE DATABASE pereval;

-- Подключение к базе данных
\c pereval;

-- Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    fam VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    otc VARCHAR(100),
    phone VARCHAR(20),
    CONSTRAINT unique_email UNIQUE (email)
);

-- Таблица координат
CREATE TABLE coords (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    height INTEGER NOT NULL
);

-- Таблица уровней сложности
CREATE TABLE levels (
    id SERIAL PRIMARY KEY,
    winter VARCHAR(10),
    summer VARCHAR(10),
    autumn VARCHAR(10),
    spring VARCHAR(10)
);

-- Таблица перевалов
CREATE TABLE pereval_added (
    id SERIAL PRIMARY KEY,
    beauty_title VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    other_titles VARCHAR(255),
    connect TEXT,
    add_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'pending', 'accepted', 'rejected')),
    user_id INTEGER REFERENCES users(id),
    coord_id INTEGER REFERENCES coords(id),
    level_id INTEGER REFERENCES levels(id),
    area_id INTEGER REFERENCES pereval_areas(id)
);

-- Таблица изображений
CREATE TABLE pereval_images (
    id SERIAL PRIMARY KEY,
    date_added TIMESTAMP DEFAULT now(),
    img BYTEA NOT NULL,
    title VARCHAR(255) NOT NULL
);

-- Связующая таблица для перевалов и изображений
CREATE TABLE pass_images (
    pass_id INTEGER REFERENCES pereval_added(id),
    image_id INTEGER REFERENCES pereval_images(id),
    PRIMARY KEY (pass_id, image_id)
);

-- Таблица регионов 
CREATE TABLE pereval_areas (
    id SERIAL PRIMARY KEY,
    id_parent INTEGER NOT NULL,
    title TEXT
);

-- Таблица типов активности
CREATE TABLE spr_activities_types (
    id SERIAL PRIMARY KEY,
    title TEXT
);
