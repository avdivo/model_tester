#!/usr/bin/env python
"""
Модуль для сравнения эталонных и тестовых ответов с гибкими настройками.
"""

import requests
from typing import Dict, Any, List, Union
from fuzzywuzzy import fuzz
from comparison_settings import ComparisonSettings


# --- Вспомогательные функции --- #

def _compare_strings_by_similarity(control_str: str, test_str: str, threshold: int) -> bool:
    """
    Сравнивает две строки на основе процента совпадения (fuzzywuzzy).
    
    :param control_str: Эталонная строка.
    :param test_str: Тестируемая строка.
    :param threshold: Минимальный процент совпадения (0-100).
    :return: True, если процент совпадения выше или равен порогу.
    """
    return fuzz.ratio(control_str.lower(), test_str.lower()) >= threshold

def _compare_by_model(question: str, control_answer: str, model_answer: str, settings: ComparisonSettings) -> bool:
    """
    Сравнивает два текстовых ответа с помощью LLM. 
    Возвращает True, если модель считает ответы эквивалентными.
    
    ВНИМАНИЕ: Эта функция является заглушкой. 
    Для ее работы требуется реализовать логику вызова LLM.
    """
    # TODO: Реализовать логику вызова внешней LLM для семантического сравнения.
    # В качестве временной заглушки используется простое сравнение на похожесть.
    print("\nПРЕДУПРЕЖДЕНИЕ: Сравнение через модель не реализовано, используется стандартное сравнение по совпадению.\n")
    return _compare_strings_by_similarity(control_answer, model_answer, 75)


# --- Основные функции рекурсивного сравнения --- #

def _compare_recursive(
    control: Any, 
    test: Any, 
    settings: ComparisonSettings, 
    context: str
) -> bool:
    """
    Главная рекурсивная функция, ядро логики сравнения.
    Определяет тип данных и вызывает соответствующий обработчик, передавая контекст.
    
    :param control: Эталонное значение.
    :param test: Тестируемое значение.
    :param settings: Объект с настройками сравнения.
    :param context: Контекст вызова ('dict', 'list' или 'text').
    :return: True, если значения эквивалентны.
    """
    # 1. Проверка на совпадение типов
    if type(control) != type(test):
        return False

    # 2. Выбор обработчика в зависимости от типа
    if isinstance(control, dict):
        return _compare_dicts(control, test, settings)
    
    if isinstance(control, list):
        return _compare_lists(control, test, settings)

    if isinstance(control, (int, float)):
        return abs(control - test) <= settings.num_tolerance

    if isinstance(control, str):
        # В зависимости от контекста, выбираем нужный метод сравнения строк
        if context == 'dict':
            method = settings.dict_str_comparison_method
            threshold = settings.dict_str_similarity_threshold
        elif context == 'list':
            method = settings.list_str_comparison_method
            threshold = settings.list_str_similarity_threshold
        else: # context == 'text'
            method = settings.text_comparison_method
            threshold = 75 # Порог по умолчанию для одиночного текста

        # Применяем выбранный метод
        if method == 'model':
            return _compare_by_model("", control, test, settings)
        else: # similarity
            return _compare_strings_by_similarity(control, test, threshold)

    # 3. Для всех остальных простых типов (bool, None и т.д.)
    return control == test

def _compare_dicts(control: Dict[str, Any], test: Dict[str, Any], settings: ComparisonSettings) -> bool:
    """
    Специализированная функция для рекурсивного сравнения словарей.
    Проверяет, что все ключи из эталонного словаря есть в тестовом, 
    игнорируя при этом лишние ключи в тестовом.
    """
    # Проверяем, что в тестовом словаре есть все ключи из эталонного
    if not all(key in test for key in control.keys()):
        return False

    # Сравниваем значения для каждого ключа
    for key, control_value in control.items():
        test_value = test[key]
        # Вызываем рекурсивное сравнение, передавая контекст 'dict'
        if not _compare_recursive(control_value, test_value, settings, context='dict'):
            return False
            
    return True

def _compare_lists(control: List[Any], test: List[Any], settings: ComparisonSettings) -> bool:
    """
    Специализированная функция для сравнения списков как "мешков" (без учета порядка).
    """
    if len(control) != len(test):
        return False

    # Создаем копию, чтобы из нее можно было удалять элементы
    test_copy = list(test)
    
    for control_item in control:
        match_found_for_control_item = False
        # Ищем подходящий элемент в тестовом списке
        for i, test_item in enumerate(test_copy):
            # Вызываем рекурсивное сравнение, передавая контекст 'list'
            if _compare_recursive(control_item, test_item, settings, context='list'):
                match_found_for_control_item = True
                del test_copy[i] # Удаляем найденный элемент, чтобы он не участвовал в других сравнениях
                break
        
        # Если для элемента из эталонного списка не нашлось пары в тестовом
        if not match_found_for_control_item:
            return False
            
    return True


# --- Публичная функция --- #

def compare(control: Any, test: Any, settings: ComparisonSettings) -> bool:
    """
    Главная точка входа для сравнения. 
    Вызывает рекурсивную функцию с первоначальным контекстом 'text'.
    """
    return _compare_recursive(control, test, settings, context='text')
