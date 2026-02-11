"""
Демонстрация работы UDPipe dependency parsing
Показывает как анализируются проблемные фразы
"""
import sys
sys.path.insert(0, "d:\\TestProject")

print("=" * 80)
print("ДЕМОНСТРАЦИЯ UDPIPE DEPENDENCY PARSING")
print("=" * 80)
print("\nПопытка загрузить UDPipe...")

try:
    from dependency_parser import get_parser
    parser = get_parser()

    if not parser or not parser.pipeline:
        print("❌ UDPipe недоступен!")
        print("Для установки запустите: python install_udpipe.py")
        sys.exit(1)

    print("✅ UDPipe загружен успешно!")
    print(f"Модель: russian-syntagrus-ud-2.12")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    print("Для установки запустите: python install_udpipe.py")
    sys.exit(1)

# Тестовые фразы с ожидаемыми результатами
test_phrases = [
    {
        "phrase": "Детские наборы кассира",
        "expected_head": "наборы",
        "expected_genitive": True,
        "description": "ADJ + NOUN(nomn,plur) + NOUN(gent) - классическая генитивная конструкция"
    },
    {
        "phrase": "наборы кассира",
        "expected_head": "наборы",
        "expected_genitive": True,
        "description": "NOUN(nomn,plur) + NOUN(gent) - простая генитивная конструкция"
    },
    {
        "phrase": "марка машинки",
        "expected_head": "марка",
        "expected_genitive": True,
        "description": "NOUN(nomn) + NOUN(gent) - машинки в родительном падеже"
    },
    {
        "phrase": "игрушки",
        "expected_head": "игрушки",
        "expected_genitive": False,
        "description": "Одно слово в именительном падеже, множественное число"
    },
    {
        "phrase": "Развивающие игрушки",
        "expected_head": "игрушки",
        "expected_genitive": False,
        "description": "ADJ + NOUN - прилагательное согласовано с существительным"
    },
    {
        "phrase": "Игрушечный транспорт",
        "expected_head": "транспорт",
        "expected_genitive": False,
        "description": "ADJ + NOUN(uncountable) - неисчисляемое существительное"
    },
    {
        "phrase": "игрушки роботы",
        "expected_head": "игрушки",
        "expected_genitive": True,  # роботы может быть родительным падежом
        "description": "Два существительных - возможна генитивная конструкция"
    },
]

print("\n" + "=" * 80)
print("АНАЛИЗ ФРАЗ")
print("=" * 80)

success_count = 0
total_count = len(test_phrases)

for i, test in enumerate(test_phrases, 1):
    phrase = test["phrase"]
    expected_head = test["expected_head"]
    expected_genitive = test["expected_genitive"]
    description = test["description"]

    print(f"\n📝 ТЕСТ {i}/{total_count}: '{phrase}'")
    print(f"   {description}")
    print("-" * 80)

    # Анализируем
    analysis = parser.analyze_structure(phrase)

    # Проверяем результаты
    actual_head = analysis['head_noun'][0] if analysis['head_noun'] else None
    actual_genitive = analysis['has_genitive']
    structure = analysis['structure']

    # Сравниваем
    head_match = actual_head == expected_head if actual_head else False
    genitive_match = actual_genitive == expected_genitive

    if head_match and genitive_match:
        print("   ✅ РЕЗУЛЬТАТ: Правильно!")
        success_count += 1
    else:
        print("   ❌ РЕЗУЛЬТАТ: Ошибка!")

    print(f"\n   Главное слово:")
    print(f"      Ожидалось: '{expected_head}'")
    print(f"      Получено:  '{actual_head}' {'✅' if head_match else '❌'}")

    print(f"\n   Генитивный модификатор:")
    print(f"      Ожидалось: {expected_genitive}")
    print(f"      Получено:  {actual_genitive} {'✅' if genitive_match else '❌'}")

    print(f"\n   Структура: {structure}")

    # Показываем детали
    if analysis['head_noun']:
        word, node = analysis['head_noun']
        print(f"\n   Детали главного слова:")
        print(f"      Слово:    {node.form}")
        print(f"      Часть речи: {node.upos}")
        print(f"      Падеж:    {node.case}")
        print(f"      Число:    {node.number}")
        print(f"      Род:      {node.gender}")

    # Показываем все узлы
    if analysis['nodes']:
        print(f"\n   Синтаксическое дерево:")
        for node in analysis['nodes']:
            genitive_mark = "🔴 GENITIVE" if node.is_genitive() else ""
            head_mark = "⭐ HEAD" if node.is_nominative() else ""
            marks = f"  {genitive_mark} {head_mark}".strip()

            print(f"      {node.form:20s} {node.upos:5s} "
                  f"case={node.case:4s} num={node.number:4s} "
                  f"dep={node.deprel:10s} {marks}")

print("\n" + "=" * 80)
print("ИТОГИ")
print("=" * 80)
print(f"Успешных тестов: {success_count}/{total_count}")
print(f"Процент:         {(success_count/total_count*100):.1f}%")
print("=" * 80)

if success_count == total_count:
    print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    print("\n✅ UDPipe правильно определяет:")
    print("   - Главные существительные")
    print("   - Генитивные конструкции (X родительный падеж)")
    print("   - Синтаксические зависимости")
else:
    print(f"\n⚠️  {total_count - success_count} тест(ов) провалено")

print("\n" + "=" * 80)
print("КАК ЭТО ПОМОГАЕТ ВАЛИДАЦИИ:")
print("=" * 80)
print("1. 'Детские наборы кассира' - определяется генитив → НЕ МЕНЯЕМ форму")
print("2. 'игрушки' - нет генитива → можно применять правила множ. числа")
print("3. 'марка машинки' - генитив (машинки) → НЕ МЕНЯЕМ")
print("=" * 80)
