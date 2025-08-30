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
        print("Ошибка: Не найден файл наборов тестов 'test_suites.md'.")
        return

    # --- Инициализация общих счетчиков ---
    grand_total_cost = 0
    model_costs = {}

    suite_counter = 1
    while True:
        suite_heading = f"Набор тестов {suite_counter}"
        suite_text = get_section(content, suite_heading, level=1)

        if suite_text is None:
            if suite_counter == 1:
                print("В файле 'test_suites.md' не найдено ни одного набора тестов.")
            break

        print(f"\n{'='*20} Обработка: {suite_heading} {'='*20}")
        suite_total_cost = 0

        try:
            # Парсим детали набора
            description = get_section(suite_text, "Описание", 2).strip()
            allow_execution = get_section(suite_text, "Разрешить выполнение", 2).strip().lower()

            print(f"Описание: {description}")

            if allow_execution != "да":
                print("Статус: Пропущен (выполнение не разрешено)")
                suite_counter += 1
                continue

            print("Статус: Выполняется")

            config_filename = get_section(suite_text, "Конфигурация", 2).strip()
            models_str = get_section(suite_text, "Модели", 2).strip()
            tests_str = get_section(suite_text, "Тесты", 2).strip()

            # Парсим количество повторов, по умолчанию 1
            repeats = 1
            repeats_str = get_section(suite_text, "Повторы", 2)
            if repeats_str:
                try:
                    repeats = int(repeats_str.strip())
                except (ValueError, TypeError):
                    print("Предупреждение: неверное значение в поле 'Повторы'. Используется значение по умолчанию (1).")
                    repeats = 1

            # Загружаем файл конфигурации
            with open(f"configs/{config_filename}.json", "r", encoding="utf-8") as cfg_f:
                config = json.load(cfg_f)

            # Получаем списки моделей и тестов, отфильтровывая пустые строки
            models = [m.strip() for m in models_str.split(',') if m.strip()]
            tests = [t.strip() for t in tests_str.split(',') if t.strip()]

            print(f"  Конфигурация: {config_filename}.json")
            print(f"  Модели для теста: {', '.join(models)}")
            print(f"  Файлы тестов: {"".join(tests)}")
            if repeats > 1:
                print(f"  Количество повторов: {repeats}")

            # Запускаем итерации
            for model in models:
                for test in tests:
                    print(f"\n--- Тестирование. Модель: {model}, Тест: {test}.md ---")
                    for i in range(repeats):
                        # Формируем заголовок с указанием повтора, если их больше одного
                        repeat_header = f" (Повтор {i + 1}/{repeats})" if repeats > 1 else ""
                        print(f"\n--- Запуск{repeat_header} ---")
                        run_cost = run_test_iteration(model, test, config)
                        suite_total_cost += run_cost
                        grand_total_cost += run_cost
                        model_costs[model] = model_costs.get(model, 0) + run_cost
                    print(f"--- Все повторы для теста {test} завершены ---")
            
            print(f"\nСтоимость выполнения набора '{suite_heading}': ${suite_total_cost:.10f}".rstrip("0").rstrip("."))

        except AttributeError as e:
            print(f"Ошибка: не удалось разобрать структуру набора '{suite_heading}'. {e}")
            print("Убедитесь, что все поля (Описание, Разрешить выполнение, Конфигурация, Модели, Тесты) присутствуют.")
        except FileNotFoundError:
            print(f"Ошибка: файл конфигурации 'configs/{config_filename}.json' не найден.")
        except json.JSONDecodeError as e:
            print(f"Ошибка: не удалось прочитать JSON из файла конфигурации -> {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка при обработке набора '{suite_heading}': {e}")
        
        suite_counter += 1

    print(f"\n{'='*20} Все наборы тестов обработаны {'='*20}")
    print("\nОБЩАЯ СВОДКА ПО СТОИМОСТИ:")
    print(f"  - Общая стоимость всех тестов: ${grand_total_cost:.10f}".rstrip("0").rstrip("."))
    if model_costs:
        print("  - Разбивка по моделям:")
        for model, cost in model_costs.items():
            print(f"    - {model}: ${cost:.10f}".rstrip("0").rstrip("."))


if __name__ == "__main__":
    main()
