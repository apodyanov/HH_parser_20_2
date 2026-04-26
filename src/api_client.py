"""Модуль для взаимодействия с API HH.ru."""
import requests
from typing import List, Dict, Any, Optional


class HHAPIClient:
    """
    Client for HH.ru API.

    Provides methods to fetch employer and vacancy data from HH.ru API.
    """

    BASE_URL: str = 'https://api.hh.ru'

    def __init__(self, timeout: int = 30) -> None:
        """
        Initialize HH.ru API client.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self.session = requests.Session()
        # Добавляем User-Agent для идентификации клиента
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 HH-Parser/1.0 (course-work; contact: your-email@example.com)'
        })

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to HH.ru API.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            JSON response as dictionary or None if request fails.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def get_employer(self, employer_id: int) -> Optional[Dict]:
        """
        Get employer information by ID.

        Args:
            employer_id: Company ID on HH.ru.

        Returns:
            Employer data dictionary.
        """
        return self._make_request(f'employers/{employer_id}')

    def get_employer_vacancies(self, employer_id: int, per_page: int = 100) -> List[Dict]:
        """
        Get all vacancies for a specific employer.

        Args:
            employer_id: Company ID on HH.ru.
            per_page: Number of vacancies per page (max 100).

        Returns:
            List of vacancy dictionaries.
        """
        all_vacancies = []
        page = 0

        while True:
            params = {
                'employer_id': employer_id,
                'per_page': per_page,
                'page': page,
                'only_with_salary': False  # Получаем все вакансии, даже без зарплаты
            }

            data = self._make_request('vacancies', params)

            if not data or not data.get('items'):
                break

            all_vacancies.extend(data['items'])

            if page >= (data.get('pages', 1) - 1):
                break

            page += 1

        return all_vacancies


# Predefined interesting employers (IDs from hh.ru)
INTERESTING_EMPLOYERS: List[Dict[str, Any]] = [
    {'id': 1740, 'name': 'Яндекс'},
    {'id': 80, 'name': 'Альфа-Банк'},
    {'id': 15478, 'name': 'VK'},
    {'id': 3529, 'name': 'Сбер'},
    {'id': 78638, 'name': 'Тинькофф'},
    {'id': 39305, 'name': 'Ozon'},
    {'id': 2180, 'name': 'Avito'},
    {'id': 2748, 'name': 'Wildberries'},
    {'id': 3776, 'name': 'МТС'},
    {'id': 1057, 'name': 'Kaspersky'}
]