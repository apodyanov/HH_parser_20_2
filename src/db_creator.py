"""Модуль для создания базы данных и таблиц."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import Optional
from config import Config


class DBCreator:
    """
    Class for creating PostgreSQL database and tables.

    Handles database creation and table setup for employers and vacancies.
    """

    def __init__(self) -> None:
        """Initialize DBCreator with connection parameters."""
        self.db_params = Config.get_db_params()
        self.db_name = Config.DB_NAME

    def create_database(self) -> Optional[psycopg2.extensions.connection]:
        """
        Create database if it doesn't exist.

        Returns:
            Connection to the created/existing database.
        """
        # Connect to default postgres database
        conn_params = self.db_params.copy()
        conn_params['dbname'] = 'postgres'

        try:
            conn = psycopg2.connect(**conn_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            # Check if database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.db_name,))
            exists = cur.fetchone()

            if not exists:
                cur.execute(f"CREATE DATABASE {self.db_name}")
                print(f"Database '{self.db_name}' created successfully.")
            else:
                print(f"Database '{self.db_name}' already exists.")

            cur.close()
            conn.close()

            # Connect to the created/existing database
            return psycopg2.connect(**self.db_params)

        except psycopg2.Error as e:
            print(f"Error creating database: {e}")
            return None

    def create_tables(self, conn: psycopg2.extensions.connection) -> bool:
        """
        Create tables for employers and vacancies.

        Args:
            conn: Active database connection.

        Returns:
            True if tables created successfully, False otherwise.
        """
        create_employers_table = """
        CREATE TABLE IF NOT EXISTS employers (
            employer_id INTEGER PRIMARY KEY,
            employer_name VARCHAR(255) NOT NULL,
            description TEXT,
            site_url VARCHAR(255),
            area VARCHAR(100),
            logo_url VARCHAR(255)
        );
        """

        create_vacancies_table = """
        CREATE TABLE IF NOT EXISTS vacancies (
            vacancy_id INTEGER PRIMARY KEY,
            vacancy_name VARCHAR(255) NOT NULL,
            employer_id INTEGER NOT NULL,
            salary_from INTEGER,
            salary_to INTEGER,
            salary_currency VARCHAR(10),
            vacancy_url TEXT NOT NULL,
            requirement TEXT,
            responsibility TEXT,
            published_at TIMESTAMP,
            FOREIGN KEY (employer_id) REFERENCES employers(employer_id) ON DELETE CASCADE
        );
        """

        create_indexes = """
        CREATE INDEX IF NOT EXISTS idx_vacancies_employer ON vacancies(employer_id);
        CREATE INDEX IF NOT EXISTS idx_vacancies_salary ON vacancies(salary_from, salary_to);
        CREATE INDEX IF NOT EXISTS idx_vacancies_name ON vacancies(vacancy_name);
        """

        try:
            cur = conn.cursor()
            cur.execute(create_employers_table)
            cur.execute(create_vacancies_table)
            cur.execute(create_indexes)
            conn.commit()
            cur.close()
            print("Tables created successfully.")
            return True
        except psycopg2.Error as e:
            print(f"Error creating tables: {e}")
            return False

    def setup_database(self) -> Optional[psycopg2.extensions.connection]:
        """
        Complete database setup: create DB and tables.

        Returns:
            Database connection or None if setup failed.
        """
        conn = self.create_database()
        if conn and self.create_tables(conn):
            return conn
        return None