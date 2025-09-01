import json
import asyncio
from time import time
from datetime import datetime
from statistics import median
from tabulate import tabulate

from func import get_section, output
from report.check import compare
from report.calc_ball import calculate_model_score
from report.to_excel import append_record_to_excel
from providers.open_router import openrouter_async
from providers.open_router import get_model_details
from comparison_settings import ComparisonSettings


def run_test_iteration(model: str, test_name: str, config: dict) -> float:
    """
    Выполняет один полный тестовый прогон для одной модели и одного файла с тестами.
    Возвращает итоговую стоимость теста.
    """
    # --- Извлечение конфигурации ---
    param = config.get("param", {})
    response_format = config.get("response_format")
    extra_body = config.get("extra_body")

    date_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    # --- ПАРАМЕТРЫ МОДЕЛИ ---
    model_details = get_model_details(model)
    if model_details is None:
        print(f"Модель {model} не найдена. Пропускаем...")
        return 0

    price_input = float(model_details.get("pricing", {}).get("prompt", 0))
    price_output = float(model_details.get("pricing", {}).get("completion", 0))

    # --- РАЗБОР ТЕСТА ---
    test_filename = f"{test_name}.md"
    try:
        with open(f"tests/{test_filename}", "r", encoding="utf-8") as file:
            test_content = file.read()
    except FileNotFoundError:
        print(f"Файл теста 'tests/{test_filename}' не найден. Пропускаем...")
        return 0

    description = get_section(test_content, "Описание").strip()
    role = get_section(test_content, "Роль").strip()
    prompt = get_section(test_content, "Промпт")

    # Настройки сравнения элементов ответа модели
    comparison_settings = ComparisonSettings()
    settings = get_section(test_content, "Настройки")
    try:
        if settings:
            for_numbers = float(get_section(settings, "Допуск при сравнении чисел", 2).strip())
            if for_numbers:
                comparison_settings.num_tolerance = float(for_numbers)
    except:
        pass

    try:
        for_strings_text = get_section(settings, "Сравнение ответа модели текстом", 2).strip()
        if for_strings_text:
            if for_strings_text.lower() == "модель":
                comparison_settings.text_comparison_method = "model"
            else:
                _, threshold = for_strings_text.split()
                comparison_settings.text_comparison_method = "similarity"  # Метод сравнения
                comparison_settings.text_similarity_threshold = int(threshold)  # Процент похожести
    except:
        pass

    try:
        for_strings_dict = get_section(settings, "Сравнение строк в словаре", 2).strip()
        if for_strings_dict:
            if for_strings_dict.lower() == "модель":
                comparison_settings.dict_str_comparison_method = "model"
            else:
                _, threshold = for_strings_dict.split()
                comparison_settings.dict_str_comparison_method = "similarity"
                comparison_settings.dict_str_similarity_threshold = int(threshold)
    except:
        pass

    try:
        for_string_list = get_section(settings, "Сравнение строк в списке", 2).strip()
        if for_string_list:
            if for_string_list.lower() == "модель":
                comparison_settings.list_str_comparison_method = "model"
            else:
                _, threshold = for_string_list.split()
                comparison_settings.list_str_comparison_method = "similarity"
                comparison_settings.list_str_similarity_threshold = int(threshold)
    except:
        pass

    # Создаем объект настроек сравнения
    question_answer = get_section(test_content, "Тесты").strip()

    if not question_answer:
        print(f"Тест '{test_name}' не содержит вопросов и ответов. Пропускаем...")
        return 0

    # --- ВЫВОД ЗАГОЛОВКА ТЕСТА ---
    rows = [
        ["Дата", date_time],
        ["Модель", model],
        ["Ввод", f"{price_input * 1000000:.2f}$ за 1М"],
        ["Вывод", f"{price_output * 1000000:.2f}$ за 1М"],
        ["Тест", test_name],
        ["Описание", description],
    ]
    table_str = tabulate(rows, tablefmt="outline")
    output(table_str, model)

    # --- ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ---
    i = 1
    exe_sum = 0
    right_sum = 0
    times_list = []
    total_time_start = time()
    total_tokens_input = 0
    total_tokens_output = 0
    total_price = 0

    # --- ОСНОВНОЙ ЦИКЛ ПО ВОПРОСАМ ---
    while True:
        question = get_section(question_answer, f"Вопрос {i}", 2)
        answer = get_section(question_answer, f"Ответ {i}", 2)
        if not question:
            break

        question = question.strip()
        comparison_settings.question = question  # Запоминаем вопрос

        try:
            answer = answer.strip()
            dict_answer = json.loads(answer)
        except:
            dict_answer = None

        # Запрос к модели
        start_time = time()
        result = asyncio.run(openrouter_async(
            model=model,
            role=role,
            prompt=prompt + "\nВопрос:\n" + question,
            param=param,
            response_format=response_format,
            extra_body=extra_body,
        ))

        if "error" in result:
            error_message = result["error"]
            print(f"Вопрос {i} - ОШИБКА API: {error_message}")
            error_text = f"Вопрос {i}:\n{question}\n\nОШИБКА API: {error_message}"
            output(error_text, model)
            i += 1
            exe_sum += 1
            continue

        response_time = time() - start_time
        times_list.append(response_time)
        tokens_input = result.get("prompt_tokens", 0)
        tokens_output = result.get("completion_tokens", 0)
        total_tokens_input += tokens_input
        total_tokens_output += tokens_output
        price = tokens_input * price_input + tokens_output * price_output
        total_price += price

        print(f"Вопрос {i}", end=" - ")
        text = f"Вопрос {i}:\n{question}\n"
        if dict_answer is not None:
            try:
                dict_result = json.loads(result.get("answer", "{{}}"))
                check = compare(dict_answer, dict_result, comparison_settings)  # Проверка ответа
                text += "Ответ модели:\n" + json.dumps(dict_result, ensure_ascii=False, indent=4)
            except:
                check = False
                text += "Ответ модели:\n" + result.get("answer", "{{}}")
        else:
            check = compare(answer, result.get("answer", ""), comparison_settings)
            text += "Ответ модели:\n" + result.get("answer", "{{}}")
        text += "\nПравильный ответ:\n" + answer

        right = ("ВЕРНО" if check else "ОШИБКА")
        output(text, model)
        print(right, f" (Время: {response_time:.2f})")

        rows_q = [
            ["Проверка", right],
            ["Токенов Ввод", tokens_input],
            ["Токенов Вывод", tokens_output],
            ["Цена запроса", f"{price:.10f}".rstrip('0').rstrip('.')],
            ["Время выполнения", f"{response_time:.2f}"],
        ]
        table_str_q = tabulate(rows_q, tablefmt="outline", disable_numparse=True)
        output(table_str_q, model)

        i += 1
        exe_sum += 1
        if check:
            right_sum += 1

    # --- ПОДВЕДЕНИЕ ИТОГОВ ---
    if exe_sum == 0:
        print("Не было выполнено ни одного вопроса.")
        return 0

    percent_correct = int(right_sum / exe_sum * 100)
    median_latency = median(times_list) if times_list else 0
    score = calculate_model_score(exe_sum, right_sum, median_latency)

    text_total = "\nИТОГ:\n"
    rows_total = [
        ["Всего вопросов", exe_sum],
        ["Правильных ответов", right_sum],
        ["Процент правильных ответов", percent_correct],
        ["Баллов за тест", score],
        ["Токенов Ввод", total_tokens_input],
        ["Токенов Вывод", total_tokens_output],
        ["Цена", f"{total_price:.10f}".rstrip('0').rstrip('.')],
        ["Время выполнения", f"{time() - total_time_start:.2f}"],
    ]
    table_str_total = tabulate(rows_total, tablefmt="outline", disable_numparse=True)
    sep = "\n" + "/\\" * 40
    output(text_total + table_str_total + sep, model)

    print(f"\nИтоги по тесту '{test_name}' для модели '{model}':")
    print(f"Медианное время выполнения - {median_latency:.2f}")
    print(f"Процент правильных ответов - {percent_correct}")
    print(f"Баллов за тест - {score}")
    print(f"Цена - {total_price:.10f}".rstrip('0').rstrip('.'))

    append_record_to_excel(
        model=model,
        test=test_name,
        median_latency=median_latency,
        percent_correct=int(right_sum / exe_sum * 100),
        score=score,
        price=total_price
    )

    return total_price

