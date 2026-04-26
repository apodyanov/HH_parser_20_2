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

    def drop_database(self) -> bool:
        """
        Drop database if it exists.

        Returns:
            True if database was dropped or didn't exist, False on error.
        """
        # Connect to default postgres database
        conn_params = self.db_params.copy()
        conn_params['dbname'] = 'postgres'

        try:
            conn = psycopg2.connect(**conn_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            # Terminate all connections to the database
            cur.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{self.db_name}'
                AND pid <> pg_backend_pid();
            """)

            # Drop database if exists
            cur.execute(f"DROP DATABASE IF EXISTS {self.db_name}")
            print(f"Database '{self.db_name}' dropped successfully (if existed).")

            cur.close()
            conn.close()
            return True

        except psycopg2.Error as e:
            print(f"Error dropping database: {e}")
            return False

    def create_database(self, drop_if_exists: bool = False) -> Optional[psycopg2.extensions.connection]:
        """
        Create database if it doesn't exist.

        Args:
            drop_if_exists: If True, drop existing database before creating.

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

            # Drop database if requested and it exists
            if drop_if_exists:
                # Terminate all connections to the database
                cur.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{self.db_name}'
                    AND pid <> pg_backend_pid();
                """)

                # Drop database if exists
                cur.execute(f"DROP DATABASE IF EXISTS {self.db_name}")
                print(f"Database '{self.db_name}' dropped successfully.")

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

    def create_tables(self, conn: psycopg2.extensions.connection, drop_tables_first: bool = False) -> bool:
        """
        Create tables for employers and vacancies.

        Args:
            conn: Active database connection.
            drop_tables_first: If True, drop existing tables before creating.

        Returns:
            True if tables created successfully, False otherwise.
        """
        # Drop tables if requested
        if drop_tables_first:
            drop_tables_query = """
            DROP TABLE IF EXISTS vacancies CASCADE;
            DROP TABLE IF EXISTS employers CASCADE;
            """
            try:
                cur = conn.cursor()
                cur.execute(drop_tables_query)
                conn.commit()
                cur.close()
                print("Existing tables dropped successfully.")
            except psycopg2.Error as e:
                print(f"Error dropping tables: {e}")
                return False

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
            vacancy_id SERIAL PRIMARY KEY,
            vacancy_name VARCHAR(255) NOT NULL,
            employer_id INTEGER NOT NULL,
            salary_from INTEGER,
            salary_to INTEGER,
            salary_currency VARCHAR(10),
            vacancy_url TEXT NOT NULL UNIQUE,
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

    def setup_database(self, drop_db_first: bool = False, drop_tables_first: bool = False) -> Optional[
        psycopg2.extensions.connection]:
        """
        Complete database setup: drop (optional), create DB and tables.

        Args:
            drop_db_first: If True, drop entire database before creating.
            drop_tables_first: If True, drop tables before creating (keeps database).

        Returns:
            Database connection or None if setup failed.
        """
        conn = None

        if drop_db_first:
            # Drop database first (this will disconnect)
            if not self.drop_database():
                print("Warning: Could not drop database, continuing...")
            # Create fresh database
            conn = self.create_database(drop_if_exists=False)
        else:
            # Normal creation without dropping database
            conn = self.create_database(drop_if_exists=False)

        if conn:
            # Create tables with optional drop
            if self.create_tables(conn, drop_tables_first=drop_tables_first):
                return conn

        return None

    def reset_database(self) -> Optional[psycopg2.extensions.connection]:
        """
        Completely reset database (drop and recreate everything).

        This is a convenience method for full database reset during development.

        Returns:
            Database connection or None if reset failed.
        """
        print("\n🔄 Полный сброс базы данных...")
        return self.setup_database(drop_db_first=True, drop_tables_first=False)


# Для обратной совместимости с существующим кодом
def create_database_with_drop(self, drop_if_exists: bool = False) -> Optional[psycopg2.extensions.connection]:
    """
    Alias for create_database method with drop_if_exists parameter.

    Args:
        drop_if_exists: If True, drop existing database before creating.

    Returns:
        Database connection.
    """
    return self.create_database(drop_if_exists=drop_if_exists)
