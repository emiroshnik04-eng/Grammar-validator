#!/usr/bin/env python3
"""
Test integration of linguistic_rules.py into check_catalog.py
"""

from check_catalog import (
    ensure_category_format,
    check_param_name_agreement,
    normalize_other_pattern
)

def test_categories():
    """Test category validation with linguistic analysis"""
    print("=" * 60)
    print("ТЕСТ КАТЕГОРИЙ")
    print("=" * 60)

    tests = [
        # Должны исправиться
        ("игрушки", "Игрушки", "Капитализация одного слова"),
        ("наборы кассира", "Наборы кассира", "Генитивная конструкция - только капитализация"),
        ("игрушечный транспорт", "Игрушечный транспорт", "Неисчисляемое - только капитализация"),
        ("Развивающие Игрушки", "Развивающие игрушки", "Второе слово строчными"),

        # НЕ должны меняться
        ("Детские наборы кассира", None, "Правильная генитивная конструкция"),
        ("Игрушечный транспорт", None, "Неисчисляемое уже правильно"),
        ("USB кабели", None, "Аббревиатура"),
    ]

    passed = 0
    failed = 0

    for original, expected, description in tests:
        result = ensure_category_format(original)

        if expected is None:
            # Ожидаем что НЕ изменится
            if result is None:
                print(f"✅ {description}")
                print(f"   '{original}' → без изменений")
                passed += 1
            else:
                print(f"❌ {description}")
                print(f"   '{original}' → '{result[1]}' (ожидалось: без изменений)")
                failed += 1
        else:
            # Ожидаем конкретное исправление
            if result and result[1] == expected:
                print(f"✅ {description}")
                print(f"   '{original}' → '{result[1]}'")
                passed += 1
            else:
                actual = result[1] if result else "без изменений"
                print(f"❌ {description}")
                print(f"   '{original}' → '{actual}' (ожидалось: '{expected}')")
                failed += 1

    print()
    print(f"Пройдено: {passed}/{len(tests)}")
    print()
    return failed == 0


def test_param_names():
    """Test parameter name agreement"""
    print("=" * 60)
    print("ТЕСТ НАЗВАНИЙ ПАРАМЕТРОВ")
    print("=" * 60)

    tests = [
        # Должны исправиться
        ("тип фигурка", "тип фигурки", "Родительный падеж"),
        ("марка машинка", "марка машинки", "Родительный падеж"),
        ("цвет корпус", "цвет корпуса", "Родительный падеж"),

        # НЕ должны меняться
        ("марка машинки", None, "Уже в родительном падеже"),
        ("тип фигурки", None, "Уже в родительном падеже"),
        ("цвет", None, "Одно слово"),
    ]

    passed = 0
    failed = 0

    for original, expected, description in tests:
        result = check_param_name_agreement(original)

        if expected is None:
            if result is None:
                print(f"✅ {description}")
                print(f"   '{original}' → без изменений")
                passed += 1
            else:
                print(f"❌ {description}")
                print(f"   '{original}' → '{result[1]}' (ожидалось: без изменений)")
                failed += 1
        else:
            if result and result[1] == expected:
                print(f"✅ {description}")
                print(f"   '{original}' → '{result[1]}'")
                passed += 1
            else:
                actual = result[1] if result else "без изменений"
                print(f"❌ {description}")
                print(f"   '{original}' → '{actual}' (ожидалось: '{expected}')")
                failed += 1

    print()
    print(f"Пройдено: {passed}/{len(tests)}")
    print()
    return failed == 0


def test_other_pattern():
    """Test 'Другой' pattern with singularization"""
    print("=" * 60)
    print("ТЕСТ ПАТТЕРНА 'ДРУГОЙ'")
    print("=" * 60)

    tests = [
        # Должны исправиться
        ("марка машинки", "Другой марка машинки", "Другая марка машинки", "Женский род"),
        ("особенности", "Другая особенности", "Другая особенность", "Сингуляризация"),
        ("цвет", "другой цвет", "Другой цвет", "Капитализация"),

        # Правильные (уже согласованы)
        ("тип игрушки", "Другой тип игрушки", None, "Уже правильно - мужской род"),
    ]

    passed = 0
    failed = 0

    for param_name, value, expected, description in tests:
        result = normalize_other_pattern(param_name, value)

        if expected is None:
            if result is None:
                print(f"✅ {description}")
                print(f"   '{value}' → без изменений")
                passed += 1
            else:
                print(f"❌ {description}")
                print(f"   '{value}' → '{result[1]}' (ожидалось: без изменений)")
                failed += 1
        else:
            if result and result[1] == expected:
                print(f"✅ {description}")
                print(f"   '{value}' → '{result[1]}'")
                passed += 1
            else:
                actual = result[1] if result else "без изменений"
                print(f"❌ {description}")
                print(f"   '{value}' → '{actual}' (ожидалось: '{expected}')")
                failed += 1

    print()
    print(f"Пройдено: {passed}/{len(tests)}")
    print()
    return failed == 0


def main():
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ LINGUISTIC_RULES.PY")
    print("=" * 60 + "\n")

    all_passed = True
    all_passed &= test_categories()
    all_passed &= test_param_names()
    all_passed &= test_other_pattern()

    print("=" * 60)
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("❌ ЕСТЬ ПРОВАЛЕННЫЕ ТЕСТЫ")
    print("=" * 60)


if __name__ == "__main__":
    main()
