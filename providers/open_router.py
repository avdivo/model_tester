
import os
import requests
from openai import OpenAI
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")  # Получи на: https://openrouter.ai/keys


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


def openrouter(model: str = "",
               role: str = "",
               prompt: str = "",
               param: dict = None,
               response_format = None,  # response_format
               extra_body = None,  # extra_body
               ):

    # Удаление не заданных параметров
    param = {key: value for key, value in param.items() if value}

    # --- 1. Настройка клиента ---
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",  # Важно: правильный URL (без пробела в конце!)
        api_key=API_KEY,  # Получи на: https://openrouter.ai/keys
    )

    arg = {
        "model": model,
        "messages": [
            {"role": "system", "content": role},
            {"role": "user", "content": prompt}
        ],

        # --- ПАРАМЕТРЫ ГЕНЕРАЦИИ (стандартные) ---
        **param,
    }

    # --- СТРУКТУРИРОВАННЫЙ ВЫВОД ---
    if response_format:
        response_format = {key: value for key, value in response_format.items() if value}
        arg["response_format"] = response_format


    # --- ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ (extra_body) ---
    if extra_body:
        extra_body = {key: value for key, value in extra_body.items() if value}
        arg["extra_body"] = extra_body

    try:
        completion = client.chat.completions.create(**arg)
        result = {
            # Ответ модели
            "answer": completion.choices[0].message.content,

            # Токены
            "prompt_tokens": completion.usage.prompt_tokens,  # Вход
            "completion_tokens": completion.usage.completion_tokens,  # Выход
        }
        return result
    except Exception as e:
        return {"error": str(e)}
