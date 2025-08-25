import json
from datetime import datetime

from func import get_section
from providers.open_router import get_model_details


model = """
mistralai/codestral-2508
""".strip()

test_name = """
get_metadata
""".strip()

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
response_format = {
    "response_format": None,  # {"type": "json_object"} Только если модель поддерживает JSON mode
    "logprobs": None,          # Возвращать лог-вероятности токенов
    "top_logprobs": None,          # Сколько топ-токенов возвращать (если logprobs=True)
}

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

date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- ПАРАМЕТРЫ МОДЕЛИ ---
# Определяем существование модели и ее параметры
model_details = get_model_details(model)
if model_details is None:
    print(f"Модель {model} не найдена.")
    exit(1)

# Цены на ввод/вывод модели за 1M токенов
price_input = float(model_details.get("pricing", {}).get("prompt", 0)) * 1000000
price_output = float(model_details.get("pricing", {}).get("completion", 0)) * 1000000

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
while True:
    question = get_section(question_answer, f"Вопрос {i}").strip()
    answer = get_section(question_answer, f"Ответ {i}").strip()
    if not question:
        break
    # Выясняем, должен ли быть ответ json
    try:
        dict_answer = json.loads(answer)
    except:
        dict_answer = None

    # Запрос к модели


print(date_time)
print(model)
print(f"Ввод {price_input:.2f}$ за 1М, Вывод {price_output:.2f}$ за 1М")
print(test_name)
print(description)
print(question_answer)



