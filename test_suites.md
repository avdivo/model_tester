# Набор тестов 1
## Описание
Тестирование проверки модели моделью
## Разрешить выполнение
нет
## Повторы
2
## Конфигурация
standard
## Модели
mistralai/codestral-2508, mistralai/ministral-3b, mistralai/mistral-small
## Тесты
test_model_check

# Набор тестов 2
## Описание
Тестирование получения метаданных из запроса
## Разрешить выполнение
нет
## Повторы
2
## Конфигурация
standard
## Модели
mistralai/codestral-2508, meta-llama/llama-3.2-3b-instruct, meta-llama/llama-3.2-1b-instruct,
liquid/lfm-7b, mistralai/mistral-nemo, meta-llama/llama-3.1-8b-instruct, liquid/lfm-3b
## Тесты
get_metadata

# Набор тестов 3
## Описание
Откуда куда ехать
## Разрешить выполнение
да
## Повторы
1
## Конфигурация
standard
## Модели
mistralai/ministral-3b, mistralai/codestral-2508, google/gemini-2.5-flash-lite-preview-06-17, 
meta-llama/llama-3.2-3b-instruct
## Тесты
for_nearest_bus