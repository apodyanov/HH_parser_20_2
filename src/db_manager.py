"""Module for database management and queries."""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
from config import Config


class DBManager:
    """
    Manager class for database operations.

    Provides methods to interact with employer and vacancy data in PostgreSQL.
    """

    def __init__(self) -> None:
        """Initialize DBManager with database connection."""
        self.db_params = Config.get_db_params()
        self.conn = None

    def _get_connection(self) -> psycopg2.extensions.connection:
        """
        Get database connection (creates new if not exists).

        Returns:
            Active database connection.
        """
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(**self.db_params)
        return self.conn

    def close_connection(self) -> None:
        """Close database connection if open."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.conn = None

    def insert_employer(self, employer_data: Dict[str, Any]) -> bool:
        """
        Insert employer data into database.

        Args:
            employer_data: Dictionary with employer information.

        Returns:
            True if insertion successful, False otherwise.
        """
        query = """
        INSERT INTO employers (employer_id, employer_name, description, site_url, area, logo_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (employer_id) DO UPDATE SET
            employer_name = EXCLUDED.employer_name,
            description = EXCLUDED.description,
            site_url = EXCLUDED.site_url,
            area = EXCLUDED.area,
            logo_url = EXCLUDED.logo_url
        """

        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(query, (
                employer_data.get('id'),
                employer_data.get('name'),
                employer_data.get('description'),
                employer_data.get('site_url'),
                employer_data.get('area', {}).get('name') if employer_data.get('area') else None,
                employer_data.get('logo_urls', {}).get('240') if employer_data.get('logo_urls') else None
            ))
            conn.commit()
            cur.close()
            return True
        except psycopg2.Error as e:
            print(f"Error inserting employer: {e}")
            return False

    def insert_vacancy(self, vacancy_data: Dict[str, Any], employer_id: int) -> bool:
        """
        Insert vacancy data into database.

        Args:
            vacancy_data: Dictionary with vacancy information.
            employer_id: Associated employer ID.

        Returns:
            True if insertion successful, False otherwise.
        """
        query = """
        INSERT INTO vacancies (
            vacancy_name, employer_id, 
            salary_from, salary_to, salary_currency, 
            vacancy_url, requirement, responsibility, published_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (vacancy_url) DO UPDATE SET
            vacancy_name = EXCLUDED.vacancy_name,
            salary_from = EXCLUDED.salary_from,
            salary_to = EXCLUDED.salary_to,
            salary_currency = EXCLUDED.salary_currency,
            requirement = EXCLUDED.requirement,
            responsibility = EXCLUDED.responsibility,
            published_at = EXCLUDED.published_at
        """

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute(query, (
                vacancy_data.get('vacancy_name'),
                employer_id,
                vacancy_data.get('salary_from'),
                vacancy_data.get('salary_to'),
                vacancy_data.get('salary_currency'),
                vacancy_data.get('vacancy_url'),
                vacancy_data.get('requirement'),
                vacancy_data.get('responsibility'),
                vacancy_data.get('published_at')
            ))
            conn.commit()
            cur.close()
            return True
        except psycopg2.Error as e:
            print(f"Error inserting vacancy: {e}")
            conn.rollback()
            return False

    def get_companies_and_vacancies_count(self) -> List[Dict[str, Any]]:
        """
        Get list of all companies with vacancy count.

        Returns:
            List of dictionaries with company name and vacancy count.
        """
        query = """
        SELECT 
            e.employer_name as company_name,
            COUNT(v.vacancy_id) as vacancy_count
        FROM employers e
        LEFT JOIN vacancies v ON e.employer_id = v.employer_id
        GROUP BY e.employer_id, e.employer_name
        ORDER BY vacancy_count DESC, company_name
        """

        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query)
            results = cur.fetchall()
            cur.close()

            # Convert to regular dicts for display
            return [dict(row) for row in results]
        except psycopg2.Error as e:
            print(f"Error getting companies and vacancies count: {e}")
            return []

    def get_all_vacancies(self) -> List[Dict[str, Any]]:
        """
        Get all vacancies with company information.

        Returns:
            List of dictionaries with vacancy details.
        """
        query = """
        SELECT 
            e.employer_name as company_name,
            v.vacancy_name as title,
            v.salary_from,
            v.salary_to,
            v.salary_currency,
            v.vacancy_url as url,
            v.requirement,
            v.responsibility
        FROM vacancies v
        JOIN employers e ON v.employer_id = e.employer_id
        ORDER BY v.published_at DESC
        """

        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query)
            results = cur.fetchall()
            cur.close()
            return results
        except psycopg2.Error as e:
            print(f"Error getting all vacancies: {e}")
            return []

    def get_avg_salary(self) -> float:
        """
        Get average salary across all vacancies.

        Average is calculated using midpoint of salary range when available.

        Returns:
            Average salary as float.
        """
        query = """
        SELECT AVG(
            CASE 
                WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL THEN (salary_from + salary_to) / 2.0
                WHEN salary_from IS NOT NULL THEN salary_from
                WHEN salary_to IS NOT NULL THEN salary_to
                ELSE NULL
            END
        ) as avg_salary
        FROM vacancies
        WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
        """

        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchone()[0]
            cur.close()
            return float(result) if result else 0.0
        except psycopg2.Error as e:
            print(f"Error getting average salary: {e}")
            return 0.0

    def get_vacancies_with_higher_salary(self) -> List[Dict[str, Any]]:
        """
        Get vacancies with salary above average.

        Returns:
            List of vacancies with higher than average salary.
        """
        avg_salary = self.get_avg_salary()

        query = """
        SELECT 
            e.employer_name as company_name,
            v.vacancy_name as title,
            v.salary_from,
            v.salary_to,
            v.salary_currency,
            v.vacancy_url as url,
            CASE 
                WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL THEN (salary_from + salary_to) / 2.0
                WHEN salary_from IS NOT NULL THEN salary_from
                WHEN salary_to IS NOT NULL THEN salary_to
                ELSE NULL
            END as salary_midpoint
        FROM vacancies v
        JOIN employers e ON v.employer_id = e.employer_id
        WHERE 
            CASE 
                WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL THEN (salary_from + salary_to) / 2.0
                WHEN salary_from IS NOT NULL THEN salary_from
                WHEN salary_to IS NOT NULL THEN salary_to
                ELSE NULL
            END > %s
        ORDER BY salary_midpoint DESC
        """

        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, (avg_salary,))
            results = cur.fetchall()
            cur.close()
            return results
        except psycopg2.Error as e:
            print(f"Error getting vacancies with higher salary: {e}")
            return []

    def get_vacancies_with_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Get vacancies containing keyword in title.

        Args:
            keyword: Search keyword.

        Returns:
            List of vacancies matching the keyword.
        """
        query = """
        SELECT 
            e.employer_name as company_name,
            v.vacancy_name as title,
            v.salary_from,
            v.salary_to,
            v.salary_currency,
            v.vacancy_url as url,
            v.requirement
        FROM vacancies v
        JOIN employers e ON v.employer_id = e.employer_id
        WHERE v.vacancy_name ILIKE %s
        ORDER BY v.published_at DESC
        """

        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, (f'%{keyword}%',))
            results = cur.fetchall()
            cur.close()
            return results
        except psycopg2.Error as e:
            print(f"Error getting vacancies with keyword: {e}")
            return []