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
