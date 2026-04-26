"""Модуль для загрузки данных из подготовленного JSON-файла."""
import json
import os
from typing import List, Dict, Optional


class JSONDataLoader:
    """
    Loader for prepared HH.ru vacancies data from JSON file.
    """

    def __init__(self, json_file_path: str = "26_07_22_hh_vacancies_sample.json"):
        """
        Initialize JSON data loader.

        Args:
            json_file_path: Path to the JSON file with vacancies data.
        """
        self.json_file_path = json_file_path
        self._data = None
        self._items = None

    def load_data(self) -> Optional[List[Dict]]:
        """
        Load vacancies data from JSON file.

        Returns:
            List of vacancy dictionaries from the 'items' key or None if file not found.
        """
        try:
            # Get absolute path to file in project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_dir, self.json_file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                self._items = data
                print(f"✅ Loaded {len(data)} vacancies from {self.json_file_path}")
            elif isinstance(data, dict) and 'items' in data:
                self._items = data['items']
                print(f"✅ Loaded {len(self._items)} vacancies from {self.json_file_path}")
                print(f"   Total found: {data.get('found', len(self._items))}")
                print(f"   Pages: {data.get('pages', 1)}")
            else:
                print(f"❌ Unexpected JSON structure: {type(data)}")
                print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                return None

            self._data = data
            return self._items

        except FileNotFoundError:
            print(f"❌ File not found: {self.json_file_path}")
            print(f"   Looking for: {file_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return None

    def extract_employers(self, vacancies: List[Dict]) -> List[Dict]:
        """
        Extract unique employers from vacancies data.

        Args:
            vacancies: List of vacancy dictionaries.

        Returns:
            List of unique employer dictionaries.
        """
        employers_dict = {}

        for vacancy in vacancies:
            employer = vacancy.get('employer', {})
            if employer and employer.get('id'):
                employer_id = employer['id']
                if employer_id not in employers_dict:
                    # Handle different possible structures of employer data
                    employers_dict[employer_id] = {
                        'id': employer_id,
                        'name': employer.get('name', 'Unknown'),
                        'description': employer.get('description'),
                        'site_url': employer.get('site_url'),
                        'area': employer.get('area', {}).get('name') if employer.get('area') else None,
                        'logo_url': None
                    }

                    # Try to get logo URL from different possible structures
                    if employer.get('logo_urls'):
                        logo_urls = employer['logo_urls']
                        if isinstance(logo_urls, dict):
                            employers_dict[employer_id]['logo_url'] = logo_urls.get('240') or logo_urls.get(
                                '90') or logo_urls.get('original')
                    elif employer.get('logo_url'):
                        employers_dict[employer_id]['logo_url'] = employer['logo_url']

        print(f"📊 Extracted {len(employers_dict)} unique employers")
        return list(employers_dict.values())

    def prepare_vacancy_for_db(self, vacancy: Dict) -> Dict:
        """
        Prepare vacancy data for database insertion.

        Args:
            vacancy: Raw vacancy dictionary from JSON.

        Returns:
            Processed vacancy dictionary.
        """
        salary = vacancy.get('salary', {})
        salary_from = salary.get('from') if salary else None
        salary_to = salary.get('to') if salary else None
        salary_currency = salary.get('currency') if salary else None

        # Clean HTML tags from snippets if present
        requirement = vacancy.get('snippet', {}).get('requirement')
        responsibility = vacancy.get('snippet', {}).get('responsibility')

        if requirement:
            import re
            requirement = re.sub(r'<[^>]+>', '', requirement)
            requirement = requirement.replace('<highlighttext>', '').replace('</highlighttext>', '')
        if responsibility:
            import re
            responsibility = re.sub(r'<[^>]+>', '', responsibility)
            responsibility = responsibility.replace('<highlighttext>', '').replace('</highlighttext>', '')

        # Handle published_at date
        published_at = vacancy.get('published_at')
        if published_at:
            # PostgreSQL timestamp format - remove microseconds
            if '.' in published_at:
                published_at = published_at.split('.')[0]

        return {
            'vacancy_name': vacancy.get('name'),  # Use 'name' as vacancy name
            'employer_id': vacancy.get('employer', {}).get('id'),
            'salary_from': salary_from,
            'salary_to': salary_to,
            'salary_currency': salary_currency,
            'vacancy_url': vacancy.get('alternate_url'),  # URL for conflict detection
            'requirement': requirement,
            'responsibility': responsibility,
            'published_at': published_at
        }

    def get_employer_vacancies(self, employer_id: int) -> List[Dict]:
        """
        Get all vacancies for a specific employer from loaded data.

        Args:
            employer_id: Employer ID to filter by.

        Returns:
            List of vacancies for the employer.
        """
        if self._items is None:
            self.load_data()

        if self._items is None:
            return []

        return [v for v in self._items if v.get('employer', {}).get('id') == employer_id]

    def get_all_vacancies(self) -> List[Dict]:
        """
        Get all loaded vacancies.

        Returns:
            List of all vacancies.
        """
        if self._items is None:
            self.load_data()

        return self._items or []

    def get_statistics(self) -> Dict:
        """
        Get statistics about loaded data.

        Returns:
            Dictionary with data statistics.
        """
        if self._items is None:
            self.load_data()

        if not self._items:
            return {'total_vacancies': 0, 'total_employers': 0}

        employers = set()
        for vacancy in self._items:
            employer = vacancy.get('employer', {})
            if employer.get('id'):
                employers.add(employer['id'])

        return {
            'total_vacancies': len(self._items),
            'total_employers': len(employers),
            'has_salary': sum(1 for v in self._items if v.get('salary')),
            'has_description': sum(1 for v in self._items if v.get('snippet', {}).get('requirement'))
        }
