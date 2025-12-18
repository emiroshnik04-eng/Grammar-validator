"""
Тестовый скрипт для проверки улучшенных функций валидации.
"""

# Импортируем функции из check_catalog
import sys
sys.path.insert(0, '.')

from check_catalog import is_proper_noun_or_compound, check_case_consistency

# Тесты для is_proper_noun_or_compound
print("=== Тесты is_proper_noun_or_compound ===\n")

test_cases_proper_noun = [
    ("Детский мир", True, "Имя собственное - бренд"),
    ("Красная площадь", True, "Имя собственное - место"),
    ("Apple товары", True, "Содержит латиницу"),
    ("iPhone 15", True, "Содержит латиницу и цифры"),
    ("Игрушка", False, "Обычное слово"),
    ("Мягкая игрушка", False, "Обычное составное название"),
    ("Игрушки", False, "Обычное слово во множественном числе"),
]

for name, expected, description in test_cases_proper_noun:
    result = is_proper_noun_or_compound(name)
    status = "OK" if result == expected else "FAIL"
    print(f"{status} '{name}': {result} (ожидалось {expected}) - {description}")

print("\n=== Тесты check_case_consistency ===\n")

test_cases_case = [
    ("красный", "lowercase", None, "Соответствует lowercase"),
    ("Красный", "lowercase", ("Красный", "красный"), "Не соответствует lowercase"),
    ("Красный", "uppercase", None, "Соответствует uppercase"),
    ("красный", "uppercase", ("красный", "Красный"), "Не соответствует uppercase"),
    ("Nike", "lowercase", None, "Бренд - пропускается"),
    ("123", "lowercase", None, "Цифры - пропускается"),
]

for value, expected_case, expected_result, description in test_cases_case:
    result = check_case_consistency(value, expected_case)

    if expected_result is None:
        status = "OK" if result is None else "FAIL"
        print(f"{status} '{value}' ({expected_case}): {result} (ожидалось None) - {description}")
    else:
        if result == expected_result:
            status = "OK"
        else:
            status = "FAIL"
        print(f"{status} '{value}' ({expected_case}): {result} (ожидалось {expected_result}) - {description}")

print("\n=== Все тесты завершены ===")
