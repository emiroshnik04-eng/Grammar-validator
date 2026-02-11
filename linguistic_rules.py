"""
Лингвистические правила для русского языка
Основаны на грамматике Розенталя и OpenCorpora разметке
"""
from typing import Optional, Tuple, Dict, List
import pymorphy3

_MORPH = pymorphy3.MorphAnalyzer(lang="ru")


def _first_parse(word: str):
    """Первый разбор слова через pymorphy3"""
    parses = _MORPH.parse(word)
    return parses[0] if parses else None


class PhraseAnalyzer:
    """
    Анализ структуры русской именной фразы
    Без dependency parsing, только морфологический анализ
    """

    @staticmethod
    def is_genitive_construction(phrase: str) -> bool:
        """
        Определяет конструкцию "NOUN(nomn) + NOUN(gent)"

        Примеры генитивных конструкций:
            "наборы кассира" - NOUN(nomn,plur) + NOUN(gent,sing) ✓
            "марка машинки" - NOUN(nomn,sing) + NOUN(gent,sing) ✓
            "тип фигурки" - NOUN(nomn,sing) + NOUN(gent,sing) ✓

        НЕ генитивные:
            "игрушки" - одно слово
            "красные машинки" - ADJ + NOUN
            "тип фигурка" - оба в nominative (ОШИБКА!)
        """
        words = phrase.strip().split()

        if len(words) < 2:
            return False

        # Проверяем паттерн: первое слово NOUN(nomn), второе NOUN(gent)
        first_word = words[0]
        second_word = words[1]

        first_parse = _first_parse(first_word)
        second_parse = _first_parse(second_word)

        if not first_parse or not second_parse:
            return False

        # Первое слово: существительное в именительном падеже
        first_is_noun_nominative = (
            "NOUN" in first_parse.tag and
            "nomn" in first_parse.tag
        )

        # Второе слово: существительное в родительном падеже
        second_is_noun_genitive = (
            "NOUN" in second_parse.tag and
            "gent" in second_parse.tag
        )

        return first_is_noun_nominative and second_is_noun_genitive

    @staticmethod
    def is_adjective_noun_phrase(phrase: str) -> bool:
        """
        Определяет конструкцию "ADJ + NOUN"

        Примеры:
            "Красные машинки" ✓
            "Детские наборы" ✓
            "Игрушечный транспорт" ✓
        """
        words = phrase.strip().split()

        if len(words) < 2:
            return False

        # Ищем паттерн: прилагательное + существительное
        for i in range(len(words) - 1):
            curr_parse = _first_parse(words[i])
            next_parse = _first_parse(words[i + 1])

            if not curr_parse or not next_parse:
                continue

            is_adj = "ADJF" in curr_parse.tag or "ADJS" in curr_parse.tag
            is_noun = "NOUN" in next_parse.tag

            if is_adj and is_noun:
                return True

        return False

    @staticmethod
    def has_multiple_nouns_nominative(phrase: str) -> bool:
        """
        Проверяет есть ли несколько существительных в именительном падеже

        Если ДА → вероятно ошибка ("тип фигурка" - оба nominative)
        Если НЕТ → правильная конструкция
        """
        words = phrase.strip().split()
        nominative_nouns = 0

        for word in words:
            p = _first_parse(word)
            if p and "NOUN" in p.tag and "nomn" in p.tag:
                nominative_nouns += 1

        return nominative_nouns >= 2

    @staticmethod
    def analyze_structure(phrase: str) -> Dict:
        """
        Полный анализ структуры фразы

        Returns:
            {
                'type': 'genitive_construction' | 'adj_noun' | 'single_word' | 'compound_error',
                'is_correct': bool,
                'main_noun': str,
                'needs_genitive_fix': bool
            }
        """
        phrase = phrase.strip()
        words = phrase.split()

        if len(words) == 1:
            return {
                'type': 'single_word',
                'is_correct': True,
                'main_noun': words[0],
                'needs_genitive_fix': False
            }

        # Проверяем генитивную конструкцию
        if PhraseAnalyzer.is_genitive_construction(phrase):
            return {
                'type': 'genitive_construction',
                'is_correct': True,  # Правильная конструкция!
                'main_noun': words[0],
                'needs_genitive_fix': False
            }

        # Проверяем ADJ + NOUN
        if PhraseAnalyzer.is_adjective_noun_phrase(phrase):
            # Находим главное существительное
            main_noun = None
            for word in words:
                p = _first_parse(word)
                if p and "NOUN" in p.tag:
                    main_noun = word
                    break

            return {
                'type': 'adj_noun',
                'is_correct': True,
                'main_noun': main_noun or words[-1],
                'needs_genitive_fix': False
            }

        # Проверяем ошибочную конструкцию: два NOUN в nominative
        if PhraseAnalyzer.has_multiple_nouns_nominative(phrase):
            return {
                'type': 'compound_error',
                'is_correct': False,
                'main_noun': words[0],
                'needs_genitive_fix': True  # Второе слово нужно в генитив!
            }

        # Неизвестная структура
        return {
            'type': 'unknown',
            'is_correct': True,  # Не трогаем неизвестные паттерны
            'main_noun': words[-1],
            'needs_genitive_fix': False
        }


class GenitiveCorrector:
    """Исправление родительного падежа в составных существительных"""

    @staticmethod
    def fix_genitive_agreement(phrase: str) -> Optional[Tuple[str, str]]:
        """
        Исправляет неправильное согласование в родительном падеже

        Examples:
            "тип фигурка" → "тип фигурки"
            "марка машинка" → "марка машинки"
            "цвет корпус" → "цвет корпуса"

        НЕ исправляет правильные:
            "марка машинки" → None (уже правильно)
            "наборы кассира" → None (уже правильно)
        """
        analysis = PhraseAnalyzer.analyze_structure(phrase)

        # Исправляем только если нужен генитив
        if not analysis['needs_genitive_fix']:
            return None

        words = phrase.strip().split()
        if len(words) < 2:
            return None

        corrected_words = [words[0]]  # Первое слово не меняем
        has_changes = False

        for word in words[1:]:
            word_parse = _first_parse(word)

            if not word_parse:
                corrected_words.append(word)
                continue

            # Если это существительное НЕ в родительном падеже
            if "NOUN" in word_parse.tag and "gent" not in word_parse.tag:
                # Преобразуем в родительный падеж
                try:
                    # Сохраняем число
                    if "plur" in word_parse.tag:
                        genitive_form = word_parse.inflect({"gent", "plur"})
                    else:
                        genitive_form = word_parse.inflect({"gent", "sing"})

                    if genitive_form:
                        corrected_words.append(genitive_form.word)
                        has_changes = True
                    else:
                        corrected_words.append(word)
                except Exception:
                    corrected_words.append(word)
            else:
                # Уже в генитиве или не существительное
                corrected_words.append(word)

        if has_changes:
            corrected = " ".join(corrected_words)
            return (phrase, corrected)

        return None


class CategoryValidator:
    """Валидация категорий с учетом лингвистических правил"""

    @staticmethod
    def should_pluralize(phrase: str, mass_like_words: set) -> bool:
        """
        Определяет нужно ли преобразовывать во множественное число

        НЕ преобразуем:
        - Генитивные конструкции ("наборы кассира")
        - Неисчисляемые ("транспорт")
        - Имена собственные
        """
        phrase_lower = phrase.lower().strip()

        # Проверка списка неисчисляемых
        if phrase_lower in mass_like_words:
            return False

        # Проверка генитивной конструкции
        if PhraseAnalyzer.is_genitive_construction(phrase):
            return False  # Уже правильная конструкция!

        return True
