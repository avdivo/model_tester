import json
from func import get_section
from tester_engine import run_test_iteration

def main():
    """
    Главный управляющий скрипт.
    Читает `test_suites.md`, парсит его и запускает разрешенные наборы тестов.
    """
    try:
        with open("test_suites.md", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("Ошибка: Не найден главный файл 'test_suites.md'.")
        return

    suite_counter = 1
    while True:
        suite_heading = f"Набор тестов {suite_counter}"
        suite_text = get_section(content, suite_heading, level=1)

        # Если секция с таким номером не найдена, значит, наборы закончились
        if suite_text is None:
            if suite_counter == 1:
                print("В файле 'test_suites.md' не найдено ни одного набора тестов.")
            break

        print(f"\n{'='*20} Обработка: {suite_heading} {'='*20}")

        try:
            # Парсим детали набора с помощью get_section для подзаголовков (level=2)
            description = get_section(suite_text, "Описание", 2).strip()
            allow_execution = get_section(suite_text, "Разрешить выполнение", 2).strip().lower()

            print(f"Описание: {description}")

            if allow_execution != "да":
                print("Статус: Пропущен (выполнение не разрешено)")
                suite_counter += 1
                continue

            print("Статус: Выполняется")

            config_filename = get_section(suite_text, "Файл конфигурации", 2).strip()
            models_str = get_section(suite_text, "Модели", 2).strip()
            tests_str = get_section(suite_text, "Тесты", 2).strip()

            # Загружаем файл конфигурации
            with open(f"configs/{config_filename}.json", "r", encoding="utf-8") as cfg_f:
                config = json.load(cfg_f)

            # Получаем списки моделей и тестов
            models = [m.strip() for m in models_str.split(',')]
            tests = [t.strip() for t in tests_str.split(',')]

            print(f"  Конфигурация: {config_filename}.json")
            print(f"  Модели для теста: {models}")
            print(f"  Файлы тестов: {tests}")

            # Запускаем итерации
            for model in models:
                for test in tests:
                    print(f"\n--- Запуск: Модель [{model}], Тест [{test}] ---")
                    run_test_iteration(model, f"{test}.md", config)
                    print(f"--- Завершено: Модель [{model}], Тест [{test}] ---")

        except AttributeError as e:
            print(f"Ошибка: не удалось разобрать структуру набора '{suite_heading}'. {e}")
            print("Убедитесь, что все поля (Описание, Разрешить выполнение, Файл конфигурации, Модели, Тесты) присутствуют.")
        except FileNotFoundError:
            print(f"Ошибка: файл конфигурации 'configs/{config_filename}.json' не найден.")
        except json.JSONDecodeError as e:
            print(f"Ошибка: не удалось прочитать JSON из файла конфигурации -> {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка при обработке набора '{suite_heading}': {e}")
        
        suite_counter += 1

    print(f"\n{'='*20} Все наборы тестов обработаны {'='*20}")

if __name__ == "__main__":
    main()
