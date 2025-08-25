
import os
import requests
from openai import OpenAI
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY"),  # Получи на: https://openrouter.ai/keys


def get_model_details(model_name: str) -> Optional[Dict]:
    """
    Возвращает детали указанной модели с OpenRouter.

    :param model_name: Название модели, например: "openai/gpt-3.5-turbo"
    :return: Словарь с информацией о модели или None, если не найдена.
    """
    url = "https://openrouter.ai/api/v1/models"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        models = response.json().get("data", [])

        # Ищем нужную модель по 'id'
        for model in models:
            if model["id"] == model_name:
                return {
                    "id": model["id"],
                    "name": model.get("name", "Неизвестно"),
                    "context_length": model.get("context_length", 0),
                    "pricing": model.get("pricing", {}),
                    "capabilities": model.get("capabilities", {}),
                    "provider": model.get("provider", {}).get("name", "Неизвестно"),
                    "updated": model.get("updated", "Неизвестно")
                }
        return None  # Модель не найдена

    except requests.exceptions.RequestException as e:
        print(f"Ошибка API: {e}")
        return None

def openrouter(model: str = "", ):
    # --- 1. Настройка клиента ---
    # Не забудь установить переменную окружения или впиши ключ (не в git!)
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",  # Важно: правильный URL (без пробела в конце!)
        api_key=API_KEY,  # Получи на: https://openrouter.ai/keys
    )


    completion = client.chat.completions.create(
        # --- ОБЯЗАТЕЛЬНЫЕ ---
        model="mistralai/mistral-7b-instruct",  # Любая модель из https://openrouter.ai/models
        messages=[
            {"role": "system", "content": "Ты помощник."},
            {"role": "user", "content": "Привет!"}
        ],

        # --- ПАРАМЕТРЫ ГЕНЕРАЦИИ (стандартные) ---
        temperature=0.7,           # Контроль случайности: 0 = детерминированно, 1 = креативно
        max_tokens=512,            # Макс. токенов в ответе
        top_p=1.0,                 # Nucleus sampling — альтернатива temperature
        frequency_penalty=0.0,     # Штраф за повторение слов (-2.0 до 2.0)
        presence_penalty=0.0,      # Штраф за новые темы (-2.0 до 2.0)
        seed=None,                 # Фиксировать результат (если поддерживается)
        stop=None,                 # Строка или список строк, при которых остановить генерацию
        stream=False,              # Потоковая передача (True/False)

        # --- СТРУКТУРИРОВАННЫЙ ВЫВОД ---
        response_format={"type": "json_object"},  # Только если модель поддерживает JSON mode
        # logprobs=False,          # Возвращать лог-вероятности токенов
        # top_logprobs=3,          # Сколько топ-токенов возвращать (если logprobs=True)

        # --- ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ (extra_body) ---
        extra_body={
            "provider": {
                "id": "baseten",                         # Принудительно использовать провайдера
                # "id": "openai",                       # Или: openai, anthropic, google и др.
                "allow_fallbacks": False,                # Запретить fallback на другие провайдеры
                # "order": ["baseten", "fireworks"]     # Приоритет провайдеров
            },
            # "transforms": ["llama-3-tokenizer"],       # Для моделей, требующих особых токенизаторов
            # "route": "fallback",                      # Стратегия маршрутизации
        }
    )