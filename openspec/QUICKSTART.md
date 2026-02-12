# OpenSpec Quick Start

## Проверка валидации

```bash
# Проверить все изменения
npx openspec list

# Валидировать конкретное изменение
npx openspec validate improve-validation-rules --strict

# Показать детали изменения
npx openspec show improve-validation-rules
```

## Текущее состояние

- **Change:** `improve-validation-rules` ✓ Complete
- **Статус:** Все задачи выполнены, спецификация актуальна
- **Валидация:** Проходит успешно

## Важные файлы

- `openspec/changes/improve-validation-rules/` - активное изменение
  - `proposal.md` - описание изменения
  - `tasks.md` - список задач (все выполнены)
  - `specs/catalog-validation/spec.md` - спецификация с требованиями

## Последние улучшения

### Сохранение родительного падежа (2026-02-12)

**Проблема:** Слово "игрушки" (родительный падеж) ошибочно преобразовывалось в "игрушка" (именительный падеж)

**Решение:**
- Добавлена проверка морфологических разборов на родительный падеж единственного числа
- Если слово может быть genitive singular и стоит не в начале фразы, оно сохраняется

**Тесты:**
- ✅ "Тип плюшевой игрушки" → "Другой тип плюшевой игрушки" (родительный падеж сохранён)
- ✅ "марка машинки" → "Другая марка машинки" (родительный падеж сохранён)

**Коммиты:**
- `01e530b` - Fix genitive case preservation in normalize_other_pattern
- `2a9662c` - Update specification with genitive case preservation requirement

## Доступ через несколько дней

OpenSpec хранится локально в проекте. Инструмент будет работать всегда:

1. **Проверить изменения:** `npx openspec list`
2. **Валидировать:** `npx openspec validate <change-id> --strict`
3. **Показать детали:** `npx openspec show <change-id>`

Все данные сохранены в Git и задеплоены на GitHub. Доступ гарантирован! ✅
