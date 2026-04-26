"""
Основная точка входа.

Этот скрипт получает данные из API HH.ru, сохраняет их в базе данных PostgreSQL
и предоставляет интерактивный интерфейс для анализа данных.
"""

import time
from src.api_client import HHAPIClient, INTERESTING_EMPLOYERS
from src.db_creator import DBCreator
from src.db_manager import DBManager
from src.user_interface import run_interface


def fetch_and_store_data(api_client: HHAPIClient, db_manager: DBManager) -> None:
    """
    Fetch employer and vacancy data from API and store in database.

    Args:
        api_client: HHAPIClient instance.
        db_manager: DBManager instance.
    """
    print("\n" + "=" * 60)
    print("НАЧАЛО ЗАГРУЗКИ ДАННЫХ")
    print("=" * 60)

    total_vacancies = 0

    for employer_info in INTERESTING_EMPLOYERS:
        employer_id = employer_info['id']
        employer_name = employer_info['name']

        print(f"\n📡 Загрузка данных о компании: {employer_name}")

        # Get employer details
        employer_data = api_client.get_employer(employer_id)
        if employer_data:
            db_manager.insert_employer(employer_data)
            print(f"   ✓ Компания добавлена: {employer_data.get('name')}")
        else:
            # Fallback to minimal data
            minimal_employer = {
                'id': employer_id,
                'name': employer_name,
                'description': None,
                'site_url': None,
                'area': None,
                'logo_urls': None
            }
            db_manager.insert_employer(minimal_employer)
            print(f"   ✓ Компания добавлена (минимальные данные): {employer_name}")

        # Get vacancies
        vacancies = api_client.get_employer_vacancies(employer_id)
        print(f"   📋 Найдено вакансий: {len(vacancies)}")

        for vacancy in vacancies:
            db_manager.insert_vacancy(vacancy, employer_id)
            total_vacancies += 1

        # Be respectful to API rate limits
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"✅ ЗАГРУЗКА ЗАВЕРШЕНА")
    print(f"   Компаний добавлено: {len(INTERESTING_EMPLOYERS)}")
    print(f"   Вакансий добавлено: {total_vacancies}")
    print("=" * 60)


def main() -> None:
    """Main function to orchestrate the application."""
    print("=" * 60)
    print("ДОБРО ПОЖАЛОВАТЬ В КУРСОВУЮ РАБОТУ!")
    print("Проект: Парсер вакансий HH.ru")
    print("=" * 60)

    # Step 1: Setup database
    print("\n🔧 Настройка базы данных...")
    db_creator = DBCreator()
    conn = db_creator.setup_database()

    if not conn:
        print("❌ Не удалось настроить базу данных. Проверьте подключение к PostgreSQL.")
        return

    conn.close()

    # Step 2: Fetch and store data
    api_client = HHAPIClient()
    db_manager = DBManager()

    try:
        fetch_and_store_data(api_client, db_manager)

        # Step 3: Run interactive interface
        run_interface(db_manager)

    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем.")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")
    finally:
        db_manager.close_connection()
        print("\nСоединение с базой данных закрыто.")


if __name__ == "__main__":
    main()