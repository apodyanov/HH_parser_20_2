"""Модуль конфигурации для подключения к базе данных."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Класс конфигурации для настроек базы данных."""

    DB_NAME: str = os.getenv('DB_NAME', 'hh_ru_db')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'postgres')
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '5432')

    @classmethod
    def get_db_params(cls) -> dict:
        """Получить параметры подключения к базе данных."""
        return {
            'dbname': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'host': cls.DB_HOST,
            'port': cls.DB_PORT
        }