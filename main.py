import json
import asyncio
from time import time, sleep
from datetime import datetime
from tabulate import tabulate
from statistics import median

from func import get_section, output
from report.check import compare, compare_text
from report.calc_ball import calculate_model_score
from report.to_excel import append_record_to_excel
from providers.open_router_async import openrouter_async
from providers.open_router import get_model_details, openrouter

model = """
moonshotai/kimi-k2
""".strip()


test_name = """
get_metadata_1
""".strip()

execute_only = []  # Выполнить тесты только с этими номерами

# --- ПАРАМЕТРЫ ГЕНЕРАЦИИ (стандартные) ---
param = {
    "temperature": 0.2,  # Контроль случайности: 0: детерминированно, 1: креативно
    "max_tokens": None,  # Макс. токенов в ответе
    "top_p": None,  # Nucleus sampling — альтернатива temperature
    "frequency_penalty": None,  # Штраф за повторение слов (-2.0 до 2.0)
    "presence_penalty": None,  # Штраф за новые темы (-2.0 до 2.0)
    "seed": None,  # Фиксировать результат (если поддерживается)
    "stop": None,  # Строка или список строк, при которых остановить генерацию
    "stream": False,  # Потоковая передача (True/False)
}

# --- СТРУКТУРИРОВАННЫЙ ВЫВОД ---
response_format = None
# {
#     "response_format": {"type": "json_object"},  # Только если модель поддерживает JSON mode
#     "logprobs": None,          # Возвращать лог-вероятности токенов
#     "top_logprobs": None,          # Сколько топ-токенов возвращать (если logprobs=True)
# }

# --- ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ (extra_body) ---
extra_body = None
"""
    {
    "provider": {
        "id": "baseten",  # Принудительно использовать провайдера
        # "id": "openai",                       # Или: openai, anthropic, google и др.
        "allow_fallbacks": False,  # Запретить fallback на другие провайдеры
        # "order": ["baseten", "fireworks"]     # Приоритет провайдеров
    },
    # "transforms": ["llama-3-tokenizer"],       # Для моделей, требующих особых токенизаторов
    # "route": "fallback",                      # Стратегия маршрутизации
}
"""

date_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

# --- ПАРАМЕТРЫ МОДЕЛИ ---
# Определяем существование модели и ее параметры
model_details = get_model_details(model)
if model_details is None:
    print(f"Модель {model} не найдена.")
    exit(1)

# Цены на ввод/вывод модели за 1M токенов
price_input = float(model_details.get("pricing", {}).get("prompt", 0))
price_output = float(model_details.get("pricing", {}).get("completion", 0))

# --- РАЗБОР ТЕСТА ---
# Читаем тест из файла из папки tests
with open(f"tests/{test_name}.md", "r") as file:
    test = file.read()

# Получаем параметры из теста
description = get_section(test, "Описание").strip()
role = get_section(test, "Роль").strip()
prompt = get_section(test, "Промпт")
question_answer = get_section(test, "Тесты").strip()

# --- РАЗБОР ВОПРОСОВ/ОТВЕТОВ. ЗАПРОСЫ ---
if not question_answer:
    print("Тест не содержит вопросов и ответов.")
    exit(1)

rows = [
    ["Дата", date_time],
    ["Модель", model],
    ["Ввод", f"{price_input * 1000000:.2f}$ за 1М"],
    ["Вывод", f"{price_output * 1000000:.2f}$ за 1М"],
    ["Тест", test_name],
    ["Описание", description],
]
table_str = tabulate(rows, tablefmt="outline")  # tablefmt="plain"
output(table_str, model)  # Вывод в файл

i = 1  # Порядковый номер вопроса
exe_sum = 0  # Обрабатываемый вопрос (сколько обработано реально)
right_sum = 0  # Правильных ответов
times_list = []  # Список времени выполнения запросов
total_time_start = time()  # Общее время выполнения
total_tokens_input = 0  # Общее количество токенов
total_tokens_output = 0  # Общее количество токенов
total_price = 0  # Общая стоимость
while True:
    question = get_section(question_answer, f"Вопрос {i}", 2)
    answer = get_section(question_answer, f"Ответ {i}", 2)
    if not question:
        break

    if execute_only and i not in execute_only:
        # Выполнить только выбранные тесты
        i += 1
        continue

    question = question.strip()

    # Выясняем, должен ли быть ответ json
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

    # Подсчет результатов запроса
    response_time = time() - start_time
    times_list.append(response_time)
    tokens_input = result.get("prompt_tokens", 0)  # Вход
    tokens_output = result.get("completion_tokens", 0)  # Выход
    total_tokens_input += tokens_input  # Вход всего
    total_tokens_output += tokens_output  # Выход всего
    price = tokens_input * price_input + tokens_output * price_output  # Цена запроса
    total_price += price  # Цена всего

    # Вопрос-ответ
    print(f"Вопрос {i}", end=" - ")
    text = f"Вопрос {i}:\n{question}\n"
    if dict_answer is not None:
        # Если ответ должен быть json
        try:
            dict_result = json.loads(result.get("answer", "{}"))
            check = compare(dict_result, dict_answer)  # Сверка ответа с эталонным
            text += "Ответ модели:\n" + json.dumps(dict_result, ensure_ascii=False, indent=4)
        except:
            check = False
            text += "Ответ модели:\n" + result.get("answer", "{}")
    else:
        # Если ответ не json проверяем правильность ответа через модель
        check = compare_text(question, answer, result.get("answer", ""))
        text += "Ответ модели:\n" + result.get("answer", "{}")
    text += "\nПравильный ответ:\n" + answer

    right = ("ВЕРНО" if check else "ОШИБКА")

    output(text, model)  # Вывод текста в файл
    print(right, f" (Время: {response_time:.2f})")

    rows = [
        ["Проверка", right],
        ["Токенов Ввод", tokens_input],
        ["Токенов Вывод", tokens_output],
        ["Цена запроса", f"{price:.10f}".rstrip('0').rstrip('.')],
        ["Время выполнения", f"{response_time:.2f}"],
    ]

    table_str = tabulate(rows, tablefmt="outline", disable_numparse=True)  # tablefmt="plain"
    output(table_str, model)  # Вывод текста

    i += 1  # Следующий вопрос
    exe_sum += 1  # Увеличиваем счетчик реально обработанных вопросов
    if check:
        right_sum += 1  # Увеличиваем счетчик правильных ответов

# Подведение итогов теста
# Баллы за тест
median_latency = median(times_list) if times_list else 0  # Медианная задержка
score = calculate_model_score(exe_sum, right_sum, median_latency)

text = "\nИТОГ:\n"
rows = [
    ["Всего вопросов", exe_sum],
    ["Правильных ответов", right_sum],
    ["Баллов за тест", score],
    ["Токенов Ввод", total_tokens_input],
    ["Токенов Вывод", total_tokens_output],
    ["Цена", f"{total_price:.10f}".rstrip('0').rstrip('.')],
    ["Время выполнения", f"{time()-total_time_start:.2f}"],
]

# Формат вывода: выровненные колонки
table_str = tabulate(rows, tablefmt="outline", disable_numparse=True)  # tablefmt="plain"
sep = "\n" + "/\\" * 40
output(text + table_str + sep, model)  # Вывод текста

print("\nБаллов за тест -", score)
print("Цена -", f"{total_price:.10f}".rstrip('0').rstrip('.'))

# Запись результата теста в Excel
append_record_to_excel(
    model=model,
    test=test_name,
    median_latency=median_latency,
    percent_correct=int(right_sum / exe_sum * 100),
    score=score,
    price=total_price
)
