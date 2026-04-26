"""
Основная точка входа.

Этот скрипт получает данные из API HH.ru, сохраняет их в базе данных PostgreSQL
и предоставляет интерактивный интерфейс для анализа данных.
"""

from src.db_creator import DBCreator
from src.db_manager import DBManager
from src.user_interface import run_interface
from src.data_loader import JSONDataLoader


def load_and_store_data(db_manager: DBManager, json_loader: JSONDataLoader) -> None:
    """
    Load data from JSON file and store in database.

    Args:
        db_manager: DBManager instance.
        json_loader: JSONDataLoader instance.
    """
    print("\n" + "=" * 60)
    print("НАЧАЛО ЗАГРУЗКИ ДАННЫХ ИЗ JSON")
    print("=" * 60)

    # Load vacancies from JSON
    vacancies = json_loader.load_data()

    if not vacancies:
        print("❌ Не удалось загрузить данные из JSON файла.")
        return

    # Extract and insert employers
    employers = json_loader.extract_employers(vacancies)
    employers_count = 0

    print("\n📋 Загрузка компаний:")
    for employer in employers:
        if db_manager.insert_employer(employer):
            employers_count += 1
            print(f"   ✓ Компания добавлена: {employer.get('name')}")

    # Insert vacancies and count per employer
    print("\n📋 Загрузка вакансий:")
    vacancies_count = 0
    employer_vacancies_count = {}

    for vacancy in vacancies:
        # Prepare vacancy data
        prepared_vacancy = {
            'vacancy_name': vacancy.get('name'),
            'employer_id': vacancy.get('employer', {}).get('id'),
            'salary_from': vacancy.get('salary', {}).get('from') if vacancy.get('salary') else None,
            'salary_to': vacancy.get('salary', {}).get('to') if vacancy.get('salary') else None,
            'salary_currency': vacancy.get('salary', {}).get('currency') if vacancy.get('salary') else None,
            'vacancy_url': vacancy.get('alternate_url'),
            'requirement': vacancy.get('snippet', {}).get('requirement'),
            'responsibility': vacancy.get('snippet', {}).get('responsibility'),
            'published_at': vacancy.get('published_at')
        }

        # Clean HTML tags from requirements
        if prepared_vacancy['requirement']:
            import re
            prepared_vacancy['requirement'] = re.sub(r'<[^>]+>', '', prepared_vacancy['requirement'])
            prepared_vacancy['requirement'] = prepared_vacancy['requirement'].replace('<highlighttext>', '').replace(
                '</highlighttext>', '')

        if prepared_vacancy['responsibility']:
            import re
            prepared_vacancy['responsibility'] = re.sub(r'<[^>]+>', '', prepared_vacancy['responsibility'])
            prepared_vacancy['responsibility'] = prepared_vacancy['responsibility'].replace('<highlighttext>',
                                                                                            '').replace(
                '</highlighttext>', '')

        # Handle published_at date
        if prepared_vacancy['published_at']:
            if '.' in prepared_vacancy['published_at']:
                prepared_vacancy['published_at'] = prepared_vacancy['published_at'].split('.')[0]

        employer_id = prepared_vacancy.get('employer_id')

        if employer_id:
            if db_manager.insert_vacancy(prepared_vacancy, employer_id):
                vacancies_count += 1
                # Count vacancies per employer
                employer_name = next((e.get('name') for e in employers if e.get('id') == employer_id), str(employer_id))
                employer_vacancies_count[employer_name] = employer_vacancies_count.get(employer_name, 0) + 1

    # Show results per employer
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ЗАГРУЗКИ ПО КОМПАНИЯМ:")
    print("=" * 60)
    for employer_name, count in sorted(employer_vacancies_count.items()):
        print(f"   ✓ {employer_name}: загружено вакансий - {count}")

    print("\n" + "=" * 60)
    print(f"✅ ЗАГРУЗКА ЗАВЕРШЕНА")
    print(f"   Компаний добавлено: {employers_count}")
    print(f"   Всего вакансий добавлено: {vacancies_count}")
    print("=" * 60)


def clear_database(db_manager: DBManager) -> None:
    """Helper function to clear database tables."""
    try:
        conn = db_manager._get_connection()
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE vacancies, employers RESTART IDENTITY CASCADE")
        conn.commit()
        cur.close()
        print("   Старые данные очищены")
    except Exception as e:
        print(f"   Ошибка очистки: {e}")


def main() -> None:
    """Main function to orchestrate the application."""
    print("=" * 60)
    print("ДОБРО ПОЖАЛОВАТЬ В КУРСОВУЮ РАБОТУ!")
    print("Проект: Парсер вакансий HH.ru (на основе подготовленных данных)")
    print("=" * 60)

    # Ask user if they want to reset database
    print("\nВыберите режим работы с базой данных:")
    print("1. Обычный запуск (сохранить существующие данные)")
    print("2. Полный сброс БД (удалить и создать заново)")
    print("3. Только очистить таблицы (удалить данные, сохранить структуру)")

    mode = input("\nВаш выбор (1/2/3): ").strip()

    # Step 1: Setup database
    print("\n🔧 Настройка базы данных...")
    db_creator = DBCreator()
    conn = None

    if mode == '2':
        # Full reset: drop database and recreate
        conn = db_creator.reset_database()
    elif mode == '3':
        # Keep database, just clear tables
        conn = db_creator.setup_database(drop_db_first=False, drop_tables_first=True)
    else:
        # Normal mode: keep existing data
        conn = db_creator.setup_database(drop_db_first=False, drop_tables_first=False)

    if not conn:
        print("❌ Не удалось настроить базу данных. Проверьте подключение к PostgreSQL.")
        return

    conn.close()

    # Step 2: Load data from JSON and store
    json_loader = JSONDataLoader()
    db_manager = DBManager()

    try:
        # Check if we need to load data
        if mode == '2' or mode == '3':
            # Fresh start, need to load data
            load_and_store_data(db_manager, json_loader)
        else:
            # Check if database has data
            conn = db_manager._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM employers")
            count = cur.fetchone()[0]
            cur.close()

            if count == 0:
                print("\nБаза данных пуста. Загружаем данные...")
                load_and_store_data(db_manager, json_loader)
            else:
                # Check if vacancies exist
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM vacancies")
                vacancies_count = cur.fetchone()[0]
                cur.close()

                print(f"\n📊 В базе данных есть:")
                print(f"   Компаний: {count}")
                print(f"   Вакансий: {vacancies_count}")

                if vacancies_count == 0:
                    print("\nВакансии отсутствуют. Загружаем данные...")
                    load_and_store_data(db_manager, json_loader)
                else:
                    reload = input("\nЖелаете перезагрузить данные? (y/N): ").strip().lower()
                    if reload == 'y':
                        clear_database(db_manager)
                        load_and_store_data(db_manager, json_loader)

        # Step 3: Run interactive interface
        run_interface(db_manager)

    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем.")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_manager.close_connection()
        print("\nСоединение с базой данных закрыто.")


if __name__ == "__main__":
    main()