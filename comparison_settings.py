from dataclasses import dataclass
from typing import Literal

# Определяем типы для методов сравнения
# similarity: сравнение по проценту совпадения (fuzzywuzzy)
# model: сравнение с помощью LLM
StrComparisonMethod = Literal["similarity", "model"]

@dataclass
class ComparisonSettings:
    """
    Датакласс для хранения настроек сравнения для одного тестового прогона.
    Каждый метод может быть model или similarity. Для model числовое значение не нужно.
    Тут приведены настройки по умолчанию.
    """
    # Допуск для сравнения чисел
    num_tolerance: float = 0.01

    # Метод сравнения для строк, являющихся ответом модели (не JSON)
    text_comparison_method: StrComparisonMethod = "model"
    text_similarity_threshold: int = 0

    # Метод сравнения для строковых значений в словарях
    dict_str_comparison_method: StrComparisonMethod = "similarity"
    dict_str_similarity_threshold: int = 75

    # Метод сравнения для строковых элементов в списках
    list_str_comparison_method: StrComparisonMethod = "similarity"
    list_str_similarity_threshold: int = 100
