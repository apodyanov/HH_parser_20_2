"""Модуль для взаимодействия с API HH.ru."""
import requests
from typing import List, Dict, Any, Optional


class HHAPIClient:
    """
    Клиент для API HH.ru.

    Предоставляет методы для получения данных о работодателях и вакансиях из API HH.ru.
    """

    BASE_URL: str = 'https://api.hh.ru'

    def __init__(self, timeout: int = 30) -> None:
        """
        Инициализация API-клиента HH.ru.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Выполнение HTTP-запроса к API HH.ru.

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
                'page': page
            }

            data = self._make_request('vacancies', params)

            if not data or not data.get('items'):
                break

            all_vacancies.extend(data['items'])

            if page >= (data.get('pages', 1) - 1):
                break

            page += 1

        return all_vacancies


# Предварительно определенные работодатели (ID с сайта hh.ru)
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