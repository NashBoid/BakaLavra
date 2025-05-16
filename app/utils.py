from natasha import Doc, Segmenter, MorphVocab
from pymorphy2 import MorphAnalyzer
from app.db import get_all_tags

# Переменная для хранения тегов
VALID_TAGS = set()

PLUGIN_TYPES = {
    'инструмент': 'instrument',
    'синтезатор': 'instrument',
    'семплер': 'instrument',
    'ромплер': 'instrument',
    'эффект': 'effect',
    'компрессор': 'effect',
    'ревербератор': 'effect',
    'эквализатор': 'effect',
    'сатурация': 'effect'
}

# Инициализация компонентов Natasha
segmenter = Segmenter()
morph_vocab = MorphVocab()
morph = MorphAnalyzer()

async def load_valid_tags():
    """Загружает теги из БД при старте бота"""
    global VALID_TAGS
    VALID_TAGS = await get_all_tags()
    print(f"[INFO] Загружено тегов из БД: {len(VALID_TAGS)}")

def lemmatize(text):
    doc = Doc(text)
    doc.segment(segmenter)  # Разбиваем на токены

    lemmas = []
    for token in doc.tokens:
        if token.pos in ['PUNCT', 'SYM']:
            continue

        parsed = morph.parse(token.text)[0]
        lemma = parsed.normal_form

        if lemma not in ['.', ',', '!', '?', '—', '-', '(', ')']:
            lemmas.append(lemma)

    return lemmas

def extract_keywords(text):
    lemmas = lemmatize(text.lower())
    plugin_type = None
    tags = set()

    for lemma in lemmas:
        if lemma in PLUGIN_TYPES:
            plugin_type = PLUGIN_TYPES[lemma]
        if lemma in VALID_TAGS:
            tags.add(lemma)

    return plugin_type, list(tags)