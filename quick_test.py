"""
Быстрый тест без LanguageTool - проверяем только pymorphy3 правила
"""
from check_catalog import (
    normalize_compound_capitalization,
    ensure_category_format,
    normalize_other_pattern,
    check_param_name_agreement,
    extract_head_noun
)

print("=" * 70)
print("БЫСТРЫЙ ТЕСТ ИСПРАВЛЕНИЙ ВАЛИДАЦИИ")
print("=" * 70)

# Тест 1: Капитализация одного слова
print("\n1. ТЕСТ: Капитализация одного слова")
test_cases = [
    ("игрушки", "Игрушки"),
    ("куклы", "Куклы"),
    ("роботы", "Роботы"),
]
for original, expected in test_cases:
    result = normalize_compound_capitalization(original)
    status = "✓" if result == expected else "✗"
    print(f"   {status} '{original}' → '{result}' (ожидалось: '{expected}')")

# Тест 2: Формат категории с капитализацией
print("\n2. ТЕСТ: Формат категории (заглавная + множ.число)")
category_tests = [
    ("игрушки", "Игрушки"),  # lowercase → capitalize
    ("игрушка", "Игрушки"),  # singular → plural + capitalize
    ("Детские наборы кассира", None),  # правильно, не должно меняться
]
for original, expected_correction in category_tests:
    result = ensure_category_format(original)
    if result:
        actual = result[1]
        status = "✓" if (expected_correction and actual == expected_correction) else "✗"
        print(f"   {status} '{original}' → '{actual}' (ожидалось: {expected_correction})")
    else:
        status = "✓" if expected_correction is None else "✗"
        print(f"   {status} '{original}' → БЕЗ ИСПРАВЛЕНИЙ (ожидалось: {expected_correction})")

# Тест 3: Извлечение главного существительного
print("\n3. ТЕСТ: Извлечение главного существительного")
head_tests = [
    ("марка машинки", "марка"),  # марка (nomn) - главное, машинки (gent) - модификатор
    ("тип фигурки", "тип"),
    ("особенности", "особенности"),
    ("цвет корпуса", "цвет"),
]
for phrase, expected_head in head_tests:
    result = extract_head_noun(phrase)
    status = "✓" if result == expected_head else "✗"
    print(f"   {status} extract_head_noun('{phrase}') = '{result}' (ожидалось: '{expected_head}')")

# Тест 4: Паттерн "Другой + параметр"
print("\n4. ТЕСТ: Паттерн 'Другой/Другая/Другое + параметр'")
other_tests = [
    ("марка машинки", "Другой марка машинки", "Другая марка машинки"),  # feminine
    ("тип игрушки", "Другой тип", "Другой тип игрушки"),  # masculine
    ("особенности", "Другая особенности", "Другая особенность"),  # feminine, singularize
    ("цвет", "Другой цвет", "Другой цвет"),  # masculine
]
for param_name, value, expected in other_tests:
    result = normalize_other_pattern(param_name, value)
    if result:
        actual = result[1]
        status = "✓" if actual == expected else "✗"
        print(f"   {status} param='{param_name}', value='{value}'")
        print(f"      → '{actual}' (ожидалось: '{expected}')")
    else:
        print(f"   ✗ param='{param_name}', value='{value}' → БЕЗ ИСПРАВЛЕНИЙ")
        print(f"      (ожидалось: '{expected}')")

# Тест 5: Согласование в составных параметрах
print("\n5. ТЕСТ: Родительный падеж в составных параметрах")
agreement_tests = [
    ("тип фигурка", "тип фигурки"),
    ("марка машинка", "марка машинки"),
    ("цвет корпус", "цвет корпуса"),
]
for original, expected in agreement_tests:
    result = check_param_name_agreement(original)
    if result:
        actual = result[1]
        status = "✓" if actual == expected else "✗"
        print(f"   {status} '{original}' → '{actual}' (ожидалось: '{expected}')")
    else:
        print(f"   ✗ '{original}' → БЕЗ ИСПРАВЛЕНИЙ (ожидалось: '{expected}')")

print("\n" + "=" * 70)
print("ТЕСТ ЗАВЕРШЁН")
print("=" * 70)
