"""
Dependency parsing для русского языка с использованием UDPipe.
Анализирует синтаксическую структуру фраз для правильной валидации.
"""
import os
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import urllib.request

try:
    from ufal.udpipe import Model, Pipeline, ProcessingError
    import conllu
    UDPIPE_AVAILABLE = True
except ImportError:
    UDPIPE_AVAILABLE = False
    Model = None
    Pipeline = None
    ProcessingError = None


# Путь к модели (будет создан в .cache)
MODEL_DIR = Path.home() / ".cache" / "udpipe"
MODEL_PATH = MODEL_DIR / "russian-syntagrus-ud-2.12-230717.udpipe"
MODEL_URL = "https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-5150/russian-syntagrus-ud-2.12-230717.udpipe"


class DependencyNode:
    """Узел в дереве зависимостей"""
    def __init__(self, token: Dict):
        self.id = token.get('id', 0)
        self.form = token.get('form', '')  # слово
        self.lemma = token.get('lemma', '')  # лемма
        self.upos = token.get('upos', '')  # часть речи (NOUN, ADJ, etc)
        self.feats = token.get('feats', {}) or {}  # морфологические признаки
        self.head = token.get('head', 0)  # индекс главного слова
        self.deprel = token.get('deprel', '')  # тип зависимости (nsubj, nmod, etc)

    @property
    def case(self) -> Optional[str]:
        """Падеж: Nom, Gen, Dat, Acc, Ins, Loc"""
        return self.feats.get('Case')

    @property
    def number(self) -> Optional[str]:
        """Число: Sing, Plur"""
        return self.feats.get('Number')

    @property
    def gender(self) -> Optional[str]:
        """Род: Masc, Fem, Neut"""
        return self.feats.get('Gender')

    def is_noun(self) -> bool:
        return self.upos == 'NOUN'

    def is_adj(self) -> bool:
        return self.upos == 'ADJ'

    def is_nominative(self) -> bool:
        return self.case == 'Nom'

    def is_genitive(self) -> bool:
        return self.case == 'Gen'

    def is_plural(self) -> bool:
        return self.number == 'Plur'

    def __repr__(self):
        return f"Node({self.form}, {self.upos}, case={self.case}, num={self.number})"


class DependencyParser:
    """Parser для анализа синтаксических зависимостей"""

    def __init__(self):
        self.model = None
        self.pipeline = None

        if not UDPIPE_AVAILABLE:
            print("[DependencyParser] UDPipe not available, dependency parsing disabled")
            return

        # Загружаем модель
        if not MODEL_PATH.exists():
            self._download_model()

        try:
            self.model = Model.load(str(MODEL_PATH))
            if not self.model:
                print(f"[DependencyParser] Failed to load model from {MODEL_PATH}")
                return

            self.pipeline = Pipeline(
                self.model,
                'tokenize',  # токенизация
                Pipeline.DEFAULT,  # default options
                Pipeline.DEFAULT,  # default options
                'conllu'  # выходной формат
            )
            print(f"[DependencyParser] Loaded UDPipe model: {MODEL_PATH}")
        except Exception as e:
            print(f"[DependencyParser] Error loading model: {e}")
            self.model = None
            self.pipeline = None

    def _download_model(self):
        """Загружает модель russian-syntagrus"""
        print(f"[DependencyParser] Downloading model to {MODEL_PATH}...")
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        try:
            urllib.request.urlretrieve(MODEL_URL, str(MODEL_PATH))
            print(f"[DependencyParser] Model downloaded successfully")
        except Exception as e:
            print(f"[DependencyParser] Failed to download model: {e}")
            raise

    def parse(self, text: str) -> Optional[List[DependencyNode]]:
        """
        Парсит текст и возвращает список узлов с зависимостями.

        Args:
            text: Текст для анализа (фраза или предложение)

        Returns:
            Список DependencyNode или None при ошибке
        """
        if not self.pipeline:
            return None

        text = (text or "").strip()
        if not text:
            return None

        try:
            # Обрабатываем текст
            processed = self.pipeline.process(text)

            # Парсим CoNLL-U формат
            sentences = conllu.parse(processed)

            if not sentences or not sentences[0]:
                return None

            # Берём первое предложение (обычно одно)
            sentence = sentences[0]

            # Создаём узлы
            nodes = []
            for token in sentence:
                # Пропускаем диапазоны (multiword tokens)
                if isinstance(token['id'], tuple):
                    continue
                nodes.append(DependencyNode(token))

            return nodes

        except Exception as e:
            print(f"[DependencyParser] Parse error: {e}")
            return None

    def find_head_noun(self, text: str) -> Optional[Tuple[str, DependencyNode]]:
        """
        Находит главное существительное в фразе.

        В русском языке главное существительное:
        1. Имеет тег NOUN
        2. Находится в именительном падеже (Nominative)
        3. Является корнем или имеет минимальную глубину в дереве

        Примеры:
            "Детские наборы кассира" → ("наборы", Node(наборы, Nom, Plur))
            "игрушки" → ("игрушки", Node(игрушки, Nom, Plur))
            "Игрушечный транспорт" → ("транспорт", Node(транспорт, Nom, Sing))

        Args:
            text: Фраза для анализа

        Returns:
            (word, node) или None если не нашли
        """
        nodes = self.parse(text)
        if not nodes:
            return None

        # Ищем существительное в именительном падеже
        for node in nodes:
            if node.is_noun() and node.is_nominative():
                return (node.form, node)

        # Если нет именительного падежа, ищем любое существительное
        for node in nodes:
            if node.is_noun():
                return (node.form, node)

        return None

    def has_genitive_modifier(self, text: str) -> bool:
        """
        Проверяет, содержит ли фраза существительное в родительном падеже
        (модификатор главного слова).

        Примеры с модификатором:
            "наборы кассира" → True (кассира - Gen)
            "игрушки роботы" → True (роботы может быть Gen)
            "марка машинки" → True (машинки - Gen)

        Примеры без модификатора:
            "игрушки" → False
            "куклы" → False

        Args:
            text: Фраза для анализа

        Returns:
            True если есть генитив-модификатор
        """
        nodes = self.parse(text)
        if not nodes or len(nodes) < 2:
            return False

        # Ищем существительное в родительном падеже
        for node in nodes:
            if node.is_noun() and node.is_genitive():
                return True

        return False

    def analyze_structure(self, text: str) -> Dict:
        """
        Полный анализ структуры фразы.

        Returns:
            {
                'head_noun': (word, node),
                'has_genitive': bool,
                'nodes': List[DependencyNode],
                'structure': str  # описание структуры
            }
        """
        nodes = self.parse(text)
        if not nodes:
            return {
                'head_noun': None,
                'has_genitive': False,
                'nodes': [],
                'structure': 'unparsed'
            }

        head = self.find_head_noun(text)
        has_gen = self.has_genitive_modifier(text)

        # Определяем структуру
        if len(nodes) == 1:
            structure = 'single_word'
        elif has_gen:
            structure = 'noun_with_genitive_modifier'
        elif any(n.is_adj() for n in nodes):
            structure = 'adjective_noun_phrase'
        else:
            structure = 'compound'

        return {
            'head_noun': head,
            'has_genitive': has_gen,
            'nodes': nodes,
            'structure': structure
        }


# Глобальный экземпляр парсера
_PARSER: Optional[DependencyParser] = None


def get_parser() -> Optional[DependencyParser]:
    """Получить глобальный экземпляр парсера (ленивая инициализация)"""
    global _PARSER
    if _PARSER is None and UDPIPE_AVAILABLE:
        _PARSER = DependencyParser()
    return _PARSER
