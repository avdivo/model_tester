import json
from time import time
from datetime import datetime
from tabulate import tabulate

from func import get_section, output
from providers.open_router import get_model_details, openrouter


model = """
mistralai/codestral-2508
""".strip()

test_name = """
get_metadata
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
#     "response_format": None,  # {"type": "json_object"} Только если модель поддерживает JSON mode
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

i = 1  # Счетчик тестовых заданий
total_time_start = time()  # Общее время выполнения
total_tokens_input = 0  # Общее количество токенов
total_tokens_output = 0  # Общее количество токенов
total_price = 0  # Общая стоимость
while True:
    question = get_section(question_answer, f"Вопрос {i}", 2)
    answer = get_section(question_answer, f"Ответ {i}", 2)
    if not question:
        break

    i += 1
    if execute_only and i - 1 not in execute_only:
        # Выполнить только выбранные тесты
        continue

    question = question.strip()

    # Выясняем, должен ли быть ответ json
    try:
        answer = answer.strip()
        dict_answer = json.loads(answer)
    except:
        dict_answer = None

    rows = [
        ["Дата", date_time],
        ["Модель", model],
        ["Ввод", f"{price_input * 1000000:.2f}$ за 1М"],
        ["Вывод", f"{price_output * 1000000:.2f}$ за 1М"],
        ["Тест", test_name],
        ["Описание", description],
    ]

    # Запрос к модели
    start_time = time()
    result = openrouter(
        model=model,
        role=role,
        prompt=prompt + "\nВопрос:\n" + question,
        param=param,
        response_format=response_format,
        extra_body=extra_body,
    )

    # Формат вывода: выровненные колонки
    table_str = tabulate(rows, tablefmt="outline")  # tablefmt="plain"
    output(table_str, model)  # Вывод текста

    # Подсчет результатов запроса
    response_time = time() - start_time
    tokens_input = result.get("prompt_tokens", 0)  # Вход
    tokens_output = result.get("completion_tokens", 0)  # Выход
    total_tokens_input += tokens_input  # Вход всего
    total_tokens_output += tokens_output  # Выход всего
    price = tokens_input * price_input + tokens_output * price_output  # Цена запроса
    total_price += price  # Цена всего

    # Вопрос-ответ
    text = f"ВОПРОС: {question}\n\n"
    if dict_answer is not None:
        # Если ответ должен быть в виде json
        try:
            dict_result = json.loads(result.get("answer", "{}"))
            if dict_result == dict_answer:
                text += "--- РАВНЫ ---"
            else:
                text += "--- НЕ РАВНЫ ---"
            text += "\nОТВЕТ (модели):\n---------------\n" + json.dumps(dict_result, ensure_ascii=False, indent=4)
        except:
            text += "--- ОШИБКА ---"
            text += "ОТВЕТ (модели):\n---------------\n" + result.get("answer", "{}")
        text += "\n\nОТВЕТ (контрольный):\n--------------------\n" + json.dumps(dict_answer, ensure_ascii=False, indent=4)
    else:
        # Если ответ не json
        text += "ОТВЕТ (модели):\n---------------\n" + result.get("answer", "")
        text += "\n\nОТВЕТ (контрольный):\n--------------------\n" + answer

    output(text, model)  # Вывод текста
    rows = [
        ["Токенов Ввод", tokens_input],
        ["Токенов Вывод", tokens_output],
        ["Цена запроса", f"{price:.10f}".rstrip('0').rstrip('.')],
        ["Время выполнения", f"{response_time:.2f}"],
    ]

    # Формат вывода: выровненные колонки
    table_str = tabulate(rows, tablefmt="outline", disable_numparse=True)  # tablefmt="plain"
    output(table_str, model)  # Вывод текста

text = "\nИТОГ:\n"
rows = [
    ["Токенов Ввод", total_tokens_input],
    ["Токенов Вывод", total_tokens_output],
    ["Цена запроса", f"{total_price:.10f}".rstrip('0').rstrip('.')],
    ["Время выполнения", f"{time()-total_time_start:.2f}"],
]

# Формат вывода: выровненные колонки
table_str = tabulate(rows, tablefmt="outline", disable_numparse=True)  # tablefmt="plain"
output(text + table_str, model)  # Вывод текста




