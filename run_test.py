"""
Тестовый скрипт для проверки исправлений валидации
"""
import pandas as pd
from check_catalog import process_dataframe, write_with_highlight

# Читаем тестовый файл
df = pd.read_csv("test_validation.csv", sep=";", dtype=str)

print("=" * 60)
print("ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ВАЛИДАЦИИ")
print("=" * 60)
print("\nИсходные данные:")
print(df[['category_level_1_name', 'param_name', 'value_name']].to_string())

# Обрабатываем
df_processed = process_dataframe(df)

print("\n" + "=" * 60)
print("РЕЗУЛЬТАТЫ ВАЛИДАЦИИ")
print("=" * 60)

# Проверяем категории
print("\n1. КАТЕГОРИИ:")
for idx, row in df_processed.iterrows():
    cat1 = row.get('category_level_1_name', '')
    cat1_correct = row.get('category_level_1_name__correct', '')
    cat1_comment = row.get('category_level_1_name__comment', '')

    if cat1_correct:
        print(f"   '{cat1}' → '{cat1_correct}'")
        print(f"   Комментарий: {cat1_comment}")

# Проверяем значения параметров
print("\n2. ЗНАЧЕНИЯ ПАРАМЕТРОВ:")
for idx, row in df_processed.iterrows():
    param = row.get('param_name', '')
    value = row.get('value_name', '')
    value_correct = row.get('value_name__correct', '')
    value_comment = row.get('value_name__comment', '')

    if value_correct:
        print(f"   Параметр: {param}")
        print(f"   '{value}' → '{value_correct}'")
        print(f"   Комментарий: {value_comment}")
        print()

# Проверяем имена параметров
print("3. ИМЕНА ПАРАМЕТРОВ:")
for idx, row in df_processed.iterrows():
    param = row.get('param_name', '')
    param_correct = row.get('param_name__correct', '')
    param_comment = row.get('param_name__comment', '')

    if param_correct:
        print(f"   '{param}' → '{param_correct}'")
        print(f"   Комментарий: {param_comment}")

# Сохраняем результаты
write_with_highlight(df_processed, "test_validation_result.xlsx")
print("\n" + "=" * 60)
print("✓ Результаты сохранены в test_validation_result.xlsx")
print(f"✓ Найдено {len(df_processed)} строк с ошибками из {len(df)} исходных")
print("=" * 60)
