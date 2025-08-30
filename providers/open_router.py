"""
Асинхронный запрос к OpenRouter через aiohttp (без библиотеки openai).
Поддерживает те же параметры: model, role, prompt, param, response_format, extra_body.
"""
import os
import aiohttp
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")  # Получи на: https://openrouter.ai/keys

async def openrouter_async(
    model: str = "",
    role: str = "",
    prompt: str = "",
    param: Optional[Dict] = None,
    response_format: Optional[Dict] = None,
    extra_body: Optional[Dict] = None,
) -> Dict[str, int]:
    """
    Асинхронный запрос к OpenRouter через aiohttp.

    :param model: Название модели (обязательно)
    :param role: Системный промпт
    :param prompt: Текст от пользователя
    :param param: Доп. параметры (temperature, max_tokens и т.п.)
    :param response_format: Для JSON-ответов, например {"type": "json_object"}
    :param extra_body: Доп. поля, например {"provider": {"id": "baseten"}}
    :return: {"answer": "...", "prompt_tokens": "...", "completion_tokens": "..."}
    """
    # Базовые параметры
    param = param or {}
    args = {
        "model": model,
        "messages": [
            {"role": "system", "content": role},
            {"role": "user", "content": prompt}
        ],
        **{k: v for k, v in param.items() if v is not None}
    }

    # Добавляем опциональные поля
    if response_format:
        args["response_format"] = {k: v for k, v in response_format.items() if v}
    if extra_body:
        args["extra_body"] = {k: v for k, v in extra_body.items() if v}

    # Заголовки
    headers = {
        "Authorization": f"Bearer {API_KEY}",  # ← Замени на свой
        "Content-Type": "application/json",
        # Опционально: для рейтинга на openrouter.ai
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Мой Бот",
    }

    # Отправляем запрос
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=args,
                headers=headers
            ) as response:
                data = await response.json()
                if response.status != 200:
                    error_message = data.get("error", {}).get("message", str(data))
                    return {"error": error_message}

        # Извлекаем ответ
        answer = data["choices"][0]["message"]["content"]
        prompt_tokens = data["usage"]["prompt_tokens"]
        completion_tokens = data["usage"]["completion_tokens"]

        return {
            "answer": answer,
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
        }
    except Exception as e:
        return {"error": str(e)}


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
