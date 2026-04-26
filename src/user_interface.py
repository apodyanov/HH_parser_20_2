"""Модуль пользовательского интерфейса для взаимодействия с базой данных."""

from src.db_manager import DBManager


def display_companies_and_vacancies(db_manager: DBManager) -> None:
    """Display companies with their vacancy counts."""
    print("\n" + "=" * 60)
    print("КОМПАНИИ И КОЛИЧЕСТВО ВАКАНСИЙ")
    print("=" * 60)

    results = db_manager.get_companies_and_vacancies_count()

    if not results:
        print("Нет данных о компаниях.")
        return

    for item in results:
        print(f"🏢 {item['company_name']}: {item['vacancy_count']} вакансий")


def display_all_vacancies(db_manager: DBManager) -> None:
    """Display all vacancies with details."""
    print("\n" + "=" * 60)
    print("ВСЕ ВАКАНСИИ")
    print("=" * 60)

    results = db_manager.get_all_vacancies()

    if not results:
        print("Нет вакансий в базе данных.")
        return

    for idx, vacancy in enumerate(results, 1):
        print(f"\n{idx}. 📌 {vacancy['title']}")
        print(f"   Компания: {vacancy['company_name']}")

        if vacancy['salary_from'] or vacancy['salary_to']:
            salary_str = "   Зарплата: "
            if vacancy['salary_from']:
                salary_str += f"от {vacancy['salary_from']}"
            if vacancy['salary_to']:
                salary_str += f" до {vacancy['salary_to']}" if vacancy['salary_from'] else f"до {vacancy['salary_to']}"
            if vacancy['salary_currency']:
                salary_str += f" {vacancy['salary_currency']}"
            print(salary_str)
        else:
            print("   Зарплата: не указана")

        print(f"   Ссылка: {vacancy['url']}")

        if vacancy['requirement']:
            requirement = vacancy['requirement'][:200]
            print(f"   Требования: {requirement}...")


def display_average_salary(db_manager: DBManager) -> None:
    """Display average salary."""
    print("\n" + "=" * 60)
    print("СРЕДНЯЯ ЗАРПЛАТА ПО ВАКАНСИЯМ")
    print("=" * 60)

    avg_salary = db_manager.get_avg_salary()

    if avg_salary > 0:
        print(f"💰 Средняя зарплата: {avg_salary:,.0f} руб.")
    else:
        print("Нет данных о зарплатах.")


def display_vacancies_with_higher_salary(db_manager: DBManager) -> None:
    """Display vacancies with salary above average."""
    print("\n" + "=" * 60)
    print("ВАКАНСИИ С ЗАРПЛАТОЙ ВЫШЕ СРЕДНЕЙ")
    print("=" * 60)

    results = db_manager.get_vacancies_with_higher_salary()

    if not results:
        print("Нет вакансий с зарплатой выше средней.")
        return

    for idx, vacancy in enumerate(results, 1):
        print(f"\n{idx}. 📌 {vacancy['title']}")
        print(f"   Компания: {vacancy['company_name']}")

        salary_midpoint = vacancy.get('salary_midpoint', 0)
        if salary_midpoint:
            print(f"   Зарплата (средняя): {salary_midpoint:,.0f} {vacancy['salary_currency'] or 'руб.'}")
        print(f"   Ссылка: {vacancy['url']}")


def display_vacancies_by_keyword(db_manager: DBManager, keyword: str) -> None:
    """Display vacancies filtered by keyword."""
    print(f"\n" + "=" * 60)
    print(f"ВАКАНСИИ, СОДЕРЖАЩИЕ '{keyword.upper()}'")
    print("=" * 60)

    results = db_manager.get_vacancies_with_keyword(keyword)

    if not results:
        print(f"Не найдено вакансий, содержащих '{keyword}'.")
        return

    print(f"Найдено вакансий: {len(results)}")

    for idx, vacancy in enumerate(results, 1):
        print(f"\n{idx}. 📌 {vacancy['title']}")
        print(f"   Компания: {vacancy['company_name']}")

        if vacancy['salary_from'] or vacancy['salary_to']:
            salary_str = "   Зарплата: "
            if vacancy['salary_from']:
                salary_str += f"от {vacancy['salary_from']}"
            if vacancy['salary_to']:
                salary_str += f" до {vacancy['salary_to']}" if vacancy['salary_from'] else f"до {vacancy['salary_to']}"
            if vacancy['salary_currency']:
                salary_str += f" {vacancy['salary_currency']}"
            print(salary_str)
        else:
            print("   Зарплата: не указана")

        print(f"   Ссылка: {vacancy['url']}")


def run_interface(db_manager: DBManager) -> None:
    """
    Main user interface loop.

    Args:
        db_manager: Instance of DBManager.
    """
    while True:
        print("\n" + "=" * 60)
        print("📊 АНАЛИЗАТОР ВАКАНСИЙ HH.RU")
        print("=" * 60)
        print("1. Список компаний и количество вакансий")
        print("2. Список всех вакансий")
        print("3. Средняя зарплата по всем вакансиям")
        print("4. Вакансии с зарплатой выше средней")
        print("5. Поиск вакансий по ключевому слову")
        print("0. Выход")
        print("-" * 60)

        choice = input("Выберите действие (0-5): ").strip()

        if choice == '0':
            print("До свидания!")
            break
        elif choice == '1':
            display_companies_and_vacancies(db_manager)
        elif choice == '2':
            display_all_vacancies(db_manager)
        elif choice == '3':
            display_average_salary(db_manager)
        elif choice == '4':
            display_vacancies_with_higher_salary(db_manager)
        elif choice == '5':
            keyword = input("Введите ключевое слово для поиска: ").strip()
            if keyword:
                display_vacancies_by_keyword(db_manager, keyword)
            else:
                print("Ключевое слово не может быть пустым.")
        else:
            print("Неверный выбор. Пожалуйста, выберите 0-5.")

        input("\nНажмите Enter для продолжения...")
