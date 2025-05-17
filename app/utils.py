from natasha import Doc, Segmenter, MorphVocab
from pymorphy2 import MorphAnalyzer
from app.db import get_all_tags, get_all_types

segmenter = Segmenter()
morph_vocab = MorphVocab()
morph = MorphAnalyzer()

def lemmatize(text):
    doc = Doc(text)
    doc.segment(segmenter)

    lemmas = []
    for token in doc.tokens:
        if token.pos in ['PUNCT', 'SYM']:
            continue

        parsed = morph.parse(token.text)[0]
        lemma = parsed.normal_form

        if lemma not in ['.', ',', '!', '?', '—', '-', '(', ')']:
            lemmas.append(lemma)

    print("Я из лемматизации! - ", lemmas)

    return lemmas

async def extract_keywords(text):
    lemmas = lemmatize(text.lower())
    plugin_type = None
    tags = set()

    # Получаем все типы и теги из БД
    all_types = await get_all_types()
    all_tags = await get_all_tags()

    # Создаём словарь {лемма_типа: имя_типа}
    type_names = {t[1].lower(): t[1] for t in all_types}
    # Создаём множество тегов
    tag_names = {t[1].lower() for t in all_tags}

    for lemma in lemmas:
        if lemma in type_names:
            plugin_type = type_names[lemma]
        if lemma in tag_names:
            tags.add(lemma)

    print("Я из экстракт вордз! - ", plugin_type, tags)

    return plugin_type, list(tags)

def is_owner(user_id):
    from config import OWNER_ID
    return user_id == OWNER_ID