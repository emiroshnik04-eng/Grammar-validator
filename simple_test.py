"""
Самый простой тест - импортируем напрямую pymorphy3
"""
import pymorphy3

morph = pymorphy3.MorphAnalyzer(lang="ru")

def _first_parse(word: str):
    parses = morph.parse(word)
    return parses[0] if parses else None

def test_capitalization():
    """Тест капитализации"""
    print("=" * 60)
    print("1. ТЕСТ: normalize_compound_capitalization")
    print("=" * 60)

    # Импортируем функцию напрямую
    import sys
    sys.path.insert(0, "d:\\TestProject")

    # Меняем инициализацию LanguageTool чтобы не загружать
    import check_catalog
    check_catalog._LT = None  # Отключаем LanguageTool

    from check_catalog import normalize_compound_capitalization

    tests = [
        ("игрушки", "Игрушки"),
        ("куклы", "Куклы"),
        ("Другой Красный Цвет", "Другой красный цвет"),
        ("Игрушки-Роботы", "Игрушки-роботы"),
    ]

    for original, expected in tests:
        result = normalize_compound_capitalization(original)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{original}' → '{result}' (ожидалось: '{expected}')")

def test_extract_head():
    """Тест извлечения главного существительного"""
    print("\n" + "=" * 60)
    print("2. ТЕСТ: extract_head_noun")
    print("=" * 60)

    import sys
    sys.path.insert(0, "d:\\TestProject")
    import check_catalog
    check_catalog._LT = None
    from check_catalog import extract_head_noun

    tests = [
        ("марка машинки", "марка"),  # марка (nomn) - главное
        ("тип фигурки", "тип"),
        ("особенности", "особенности"),
    ]

    for phrase, expected in tests:
        result = extract_head_noun(phrase)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{phrase}' → '{result}' (ожидалось: '{expected}')")

        # Покажем разборы всех слов
        for word in phrase.split():
            p = _first_parse(word)
            if p:
                print(f"      '{word}': {p.tag}")

def test_other_pattern():
    """Тест паттерна Другой"""
    print("\n" + "=" * 60)
    print("3. ТЕСТ: normalize_other_pattern")
    print("=" * 60)

    import sys
    sys.path.insert(0, "d:\\TestProject")
    import check_catalog
    check_catalog._LT = None
    from check_catalog import normalize_other_pattern

    tests = [
        ("марка машинки", "Другой марка машинки", "Другая марка машинки"),
        ("особенности", "Другая особенности", "Другая особенность"),
    ]

    for param, value, expected in tests:
        result = normalize_other_pattern(param, value)
        if result:
            actual = result[1]
            status = "✓" if actual == expected else "✗"
            print(f"{status} param='{param}', value='{value}'")
            print(f"   → '{actual}' (ожидалось: '{expected}')")
        else:
            print(f"✗ param='{param}', value='{value}' → БЕЗ ИСПРАВЛЕНИЙ")

if __name__ == "__main__":
    test_capitalization()
    test_extract_head()
    test_other_pattern()
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЁН")
    print("=" * 60)
