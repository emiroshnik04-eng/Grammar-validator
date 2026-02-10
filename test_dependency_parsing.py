"""
Тест dependency parsing для валидации категорий
"""
from dependency_parser import get_parser

# Тестовые фразы
test_phrases = [
    # Простые случаи
    ("игрушки", "single word, nomn, plur"),
    ("куклы", "single word, nomn, plur"),
    ("игрушка", "single word, nomn, sing - needs plural"),

    # Конструкции с родительным падежом (НЕ ТРОГАЕМ!)
    ("Детские наборы кассира", "ADJ + NOUN(nomn,plur) + NOUN(gent) - CORRECT!"),
    ("наборы кассира", "NOUN(nomn,plur) + NOUN(gent) - CORRECT!"),
    ("игрушки роботы", "may have genitive"),
    ("марка машинки", "NOUN(nomn) + NOUN(gent) - CORRECT!"),

    # Прилагательное + существительное
    ("Развивающие игрушки", "ADJ + NOUN - check plural"),
    ("Игрушечный транспорт", "ADJ + NOUN(uncountable)"),

    # Неправильные формы
    ("детские набор", "needs plural"),
    ("игрушек", "wrong case, needs nomn+plur"),
]

print("=" * 80)
print("ТЕСТ DEPENDENCY PARSING")
print("=" * 80)

parser = get_parser()
if not parser or not parser.pipeline:
    print("ERROR: UDPipe not available!")
    exit(1)

for phrase, description in test_phrases:
    print(f"\n📝 Фраза: '{phrase}'")
    print(f"   Описание: {description}")
    print("-" * 80)

    # Анализ
    analysis = parser.analyze_structure(phrase)

    print(f"   Структура: {analysis['structure']}")
    print(f"   Есть генитив: {analysis['has_genitive']}")

    if analysis['head_noun']:
        word, node = analysis['head_noun']
        print(f"   Главное слово: '{word}' (case={node.case}, number={node.number}, gender={node.gender})")
    else:
        print(f"   Главное слово: НЕ НАЙДЕНО")

    # Показываем все узлы
    if analysis['nodes']:
        print(f"   Все узлы:")
        for node in analysis['nodes']:
            print(f"      - {node.form:20s} {node.upos:5s} case={node.case} num={node.number} head={node.head} rel={node.deprel}")

print("\n" + "=" * 80)
print("ВЫВОД:")
print("=" * 80)
print("✓ Фразы с has_genitive=True НЕ ДОЛЖНЫ изменяться (кроме капитализации)")
print("✓ Фразы без генитива проверяем: главное слово в nomn+plur")
print("=" * 80)
