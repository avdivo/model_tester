import requests
from typing import Dict, Any, List, Union
from fuzzywuzzy import fuzz

NUM_TOL = 0.01  # Максимально допустимое отличие для чисел
STR_SIM = 75  # Минимальная похожесть строк в % (0-100) (без сравнения смысла)

def compare_dicts(
    control: Dict[str, Any],
    test: Dict[str, Any],
    num_tol: float = NUM_TOL,
    str_sim: int = STR_SIM
) -> bool:
    """
    Сравнивает контрольный и тестируемый словари по значениям с допусками:
    - Числа: с заданной погрешностью (по умолчанию 0.01)
    - Строки: без учёта регистра и с размытым сравнением (fuzzy)
    - Вложенные словари: рекурсивно

    Лишние ключи в тестируемом словаре игнорируются.
    Отсутствие ключа или несоответствие значения — ошибка.

    Использует: fuzzywuzzy + python-Levenshtein (для скорости и поддержки кириллицы).

    :param control: Контрольный словарь (эталон).
    :param test: Тестируемый словарь.
    :param num_tol: Максимально допустимое отличие для чисел (по умолчанию 0.01).
    :param str_sim: Минимальная похожесть строк в % (0-100, по умолчанию 85).
    :return: True — если все обязательные поля совпадают, иначе False.
    """
    for key, expected_value in control.items():
        # Ключ должен существовать
        if key not in test:
            return False

        actual_value = test[key]

        # Если оба значения — словари, сравниваем рекурсивно
        if isinstance(expected_value, dict) and isinstance(actual_value, dict):
            if not compare_dicts(expected_value, actual_value, num_tol, str_sim):
                return False
            continue

        # Проверка типов: типы должны совпадать
        if type(expected_value) != type(actual_value):
            return False

        # Сравнение чисел с погрешностью
        if isinstance(expected_value, (int, float)):
            if abs(expected_value - actual_value) > num_tol:
                return False

        # Сравнение строк с учётом похожести (fuzzy) и без учёта регистра
        elif isinstance(expected_value, str):
            similarity = fuzz.ratio(expected_value.lower(), actual_value.lower())
            if similarity < str_sim:
                return False

        # Для остальных типов (bool, None, и т.п.) — строгое равенство
        else:
            if expected_value != actual_value:
                return False

    # Все проверки пройдены
    return True


def compare_text(
    question : str = "",
    answer: str = "",
    answer_model: str = ""
) -> str:
    """
    Запрос в выбранный агрегатор (OpenRouter или Comet API).
    Модель должна определить правильность ответа модели на вопрос
    имея эталонный ответ.
    Для строкового эталонного ответа проверяется близость ответа модели.
    Для json ответа полная схожесть или похожесть не числовых

    :param question: вопрос, от
    :param api_key: API-ключ для выбранного агрегатора
    :param prompt: Вопрос к модели, на который нужно получить только 'Yes' или 'No'
    :return: Строка с ответом ('Yes' или 'No'), очищенная от пробелов и перевода строк
    """

    # Конфигурация для каждого агрегатора: URL, заголовки и модель
    CONFIG = {
        "openrouter": {
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "headers": lambda key: {
                "Authorization": f"Bearer {key}",
                "HTTP-Referer": "http://localhost",
                "X-Title": "yes-no-test"
            },
            "model": "openai/gpt-4o-mini"  # пример; можно заменить на другую
        },
        "comet": {
            "url": "https://api.cometapi.com/v1/chat/completions",
            "headers": lambda key: {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            "model": "gpt-4o-mini"  # пример модели Comet
        }
    }

    if aggregator not in CONFIG:
        raise ValueError(f"Неизвестный агрегатор: {aggregator}")

    cfg = CONFIG[aggregator]

    # Формируем данные запроса
    data = {
        "model": cfg["model"],
        "messages": [
            {"role": "user", "content": f"Answer ONLY 'Yes' or 'No'. {prompt}"}
        ],
        "max_tokens": 3  # ограничение на длину ответа
    }

    # Выполняем HTTP POST запрос
    response = requests.post(
        cfg["url"],
        headers=cfg["headers"](api_key),
        json=data,
        timeout=15
    )
    response.raise_for_status()  # выбросить исключение при HTTP-ошибке

    # Извлекаем и возвращаем результат
    result = response.json()
    return result["choices"][0]["message"]["content"].strip()


def compare(control: Union[Dict, List, str, int, float, Any],
           test: Union[Dict, List, str, int, float, Any]) -> bool:
    """
    Универсальная функция сравнения. Принимает любые два объекта и возвращает True, если они
    считаются равными по правилам, зависящим от типа.

    :param control: Контрольное значение (эталон).
    :param test: Тестируемое значение.
    :return: True — если значения (или структуры) эквивалентны, иначе False.
    """
    # Типы не совпадают — сразу False
    if type(control) != type(test):
        return False

    # --- Словари ---
    if isinstance(control, dict):
        return compare_dicts(control, test)

    # --- Строки ---
    if isinstance(control, str):
        return compare_text(control, test)

    # --- Числа (int, float) ---
    if isinstance(control, (int, float)):
        return abs(control - test) <= NUM_TOL

    # --- Списки ---
    if isinstance(control, list):
        # Длина должна совпадать
        if len(control) != len(test):
            return False

        # Работаем с копиями, чтобы удалять совпавшие элементы
        remaining_control = control.copy()
        remaining_test = test.copy()

        # Для каждого элемента в контрольном списке ищем совпадение
        for item_ctrl in control:
            matched = False
            for item_test in remaining_test:
                if compare(item_ctrl, item_test):  # Рекурсивно используем compare
                    # Удаляем совпавшие
                    remaining_control.remove(item_ctrl)
                    remaining_test.remove(item_test)
                    matched = True
                    break
            if not matched:
                return False

        # Все элементы должны быть сопоставлены
        return len(remaining_control) == 0

    # --- Все остальные типы (bool, None, и т.п.) ---
    return control == test