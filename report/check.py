import requests
from typing import Dict, Any, List, Union
from fuzzywuzzy import fuzz
from comparison_settings import ComparisonSettings

# --- НОВЫЕ ФУНКЦИИ СРАВНЕНИЯ С УЧЕТОМ НАСТРОЕК ---

def compare_text(question: str, answer: str, answer_model: str, settings: ComparisonSettings) -> bool:
    """
    Сравнивает текстовые ответы с помощью LLM.
    (ВНИМАНИЕ: Текущая реализация - заглушка, требует доработки для реального использования,
    так как использует неопределенные переменные aggregator и api_key)
    """
    # TODO: Доработать эту функцию для реальных запросов к LLM для проверки
    # Пока что она просто использует fuzzywuzzy как запасной вариант
    similarity = fuzz.ratio(answer.lower(), answer_model.lower())
    return similarity >= 75 # Используем некий порог по умолчанию

def compare_strings(control_str: str, test_str: str, threshold: int) -> bool:
    """
    Сравнивает две строки на основе процента совпадения (fuzzywuzzy).
    """
    return fuzz.ratio(control_str.lower(), test_str.lower()) >= threshold

def compare_values(control: Any, test: Any, settings: ComparisonSettings, context: str) -> bool:
    """
    Универсальная функция сравнения двух значений с учетом контекста и настроек.
    """
    if type(control) != type(test):
        return False

    if isinstance(control, dict):
        return compare_dicts(control, test, settings)
    
    if isinstance(control, list):
        return compare_lists(control, test, settings)

    if isinstance(control, (int, float)):
        return abs(control - test) <= settings.num_tolerance

    if isinstance(control, str):
        if context == 'dict':
            if settings.dict_str_comparison_method == 'similarity':
                return compare_strings(control, test, settings.dict_str_similarity_threshold)
            else: # model
                # Заглушка для сравнения через модель
                return compare_text("", control, test, settings)
        elif context == 'list':
            if settings.list_str_comparison_method == 'similarity':
                return compare_strings(control, test, settings.list_str_similarity_threshold)
            else: # model
                return compare_text("", control, test, settings)
        else: # text
            if settings.text_comparison_method == 'similarity':
                return compare_strings(control, test, 75) # Порог по умолчанию для текста
            else: # model
                return compare_text("", control, test, settings)

    # Для всех остальных типов (bool, None)
    return control == test

def compare_dicts(control: Dict[str, Any], test: Dict[str, Any], settings: ComparisonSettings) -> bool:
    """
    Рекурсивно сравнивает два словаря с учетом настроек.
    """
    if len(control) > len(test):
        return False # Если в тестовом словаре не хватает ключей

    for key, control_value in control.items():
        if key not in test:
            return False
        test_value = test[key]
        if not compare_values(control_value, test_value, settings, context='dict'):
            return False
    return True

def compare_lists(control: List[Any], test: List[Any], settings: ComparisonSettings) -> bool:
    """
    Сравнивает два списка с учетом настроек.
    Для неупорядоченного сравнения (bag comparison).
    """
    if len(control) != len(test):
        return False

    test_copy = list(test)
    for control_item in control:
        found_match = False
        for i, test_item in enumerate(test_copy):
            if compare_values(control_item, test_item, settings, context='list'):
                found_match = True
                del test_copy[i]
                break
        if not found_match:
            return False
    return True

def compare(control: Any, test: Any, settings: ComparisonSettings) -> bool:
    """
    Главная точка входа для сравнения двух ответов (эталонного и от модели).
    """
    return compare_values(control, test, settings, context='text')
