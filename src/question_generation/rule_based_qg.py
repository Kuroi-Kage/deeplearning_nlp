import re


try:
    import spacy
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False

_SPACY_MODELS = {
    "fr": "fr_core_news_sm",
    "en": "en_core_web_sm",
}

_nlp_cache = {}

_INVALID_ANSWERS = {
    "article", "résumé", "resume", "introduction", "conclusion",
    "abstract", "chapitre", "section", "annexe", "sommaire",
    "l'", "d'", "c'", "s'", "n'", "qu'",
}


def _is_valid_answer(answer: str) -> bool:
    """Rejette les réponses trop courtes, tronquées ou trop génériques."""
    cleaned = answer.strip()

    if len(cleaned) < 3:
        return False
    if cleaned.endswith(("'", "-", "’")):
        return False
    if cleaned.lower() in _INVALID_ANSWERS:
        return False

    return True


def _load_spacy_model(lang: str):
    if lang not in _nlp_cache:
        _nlp_cache[lang] = spacy.load(_SPACY_MODELS[lang])
    return _nlp_cache[lang]


_SPACY_TEMPLATES = {
    "fr": {
        "PER": "Qui {rest} ?",
        "LOC": "Où {rest} ?",
        "GPE": "Où {rest} ?",
        "DATE": "Quand {rest} ?",
        "CARDINAL": "Combien {rest} ?",
        "ORG": "Quelle organisation {rest} ?",
    },
    "en": {
        "PERSON": "Who {rest} ?",
        "GPE": "Where {rest} ?",
        "LOC": "Where {rest} ?",
        "DATE": "When {rest} ?",
        "CARDINAL": "How many {rest} ?",
        "ORG": "Which organization {rest} ?",
    },
}


def _build_question_spacy(sentence: str, ent_text: str, ent_label: str, lang: str):
    template = _SPACY_TEMPLATES.get(lang, {}).get(ent_label)
    if not template:
        return None
    rest = sentence.replace(ent_text, "").strip().rstrip(".!?")
    rest = rest[0].lower() + rest[1:] if rest else rest
    if not rest:
        return None
    return template.format(rest=rest)


def _generate_spacy(passage: str, lang: str, max_questions: int) -> list[dict]:
    if lang not in _SPACY_MODELS:
        return []

    nlp = _load_spacy_model(lang)  # peut lever une exception -> gérée par l'appelant
    doc = nlp(passage)

    results = []
    for sent in doc.sents:
        if len(results) >= max_questions:
            break
        sent_doc = nlp(sent.text)
        for ent in sent_doc.ents:
            if ent.label_ not in _SPACY_TEMPLATES.get(lang, {}):
                continue
            question = _build_question_spacy(sent.text, ent.text, ent.label_, lang)
            if question and _is_valid_answer(ent.text):
                results.append({
                    "question": question,
                    "answer": ent.text,
                    "answer_type": ent.label_,
                    "source_sentence": sent.text.strip(),
                    "method": "spacy",
                })
                break
        if len(results) >= max_questions:
            break
    return results


_LITE_TEMPLATES = {
    "fr": {"DATE": "Quand {rest} ?", "PROPN": "Qui ou quoi {rest} ?"},
    "en": {"DATE": "When {rest} ?", "PROPN": "Who or what {rest} ?"},
}

_YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
_PROPER_NOUN_RE = re.compile(r"\b([A-ZÀ-Ý][\wÀ-ÿ'-]*(?:\s+[A-ZÀ-Ý][\wÀ-ÿ'-]*){0,2})\b")


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _build_question_lite(sentence: str, answer: str, entity_type: str, lang: str, is_first_word: bool):
    if is_first_word:
        return None  # évite de transformer le sujet en début de phrase (souvent trop générique)

    template = _LITE_TEMPLATES.get(lang, {}).get(entity_type)
    if not template:
        return None

    rest = sentence.replace(answer, "", 1).rstrip(".!?").strip()
    rest = re.sub(r"\s+", " ", rest).strip()
    if not rest or len(rest.split()) < 3:
        return None
    rest = rest[0].lower() + rest[1:]
    return template.format(rest=rest)


def _generate_lite(passage: str, lang: str, max_questions: int) -> list[dict]:
    if lang not in _LITE_TEMPLATES:
        lang = "fr"

    results = []
    for sentence in _split_sentences(passage):
        if len(results) >= max_questions:
            break

        year_match = _YEAR_RE.search(sentence)
        if year_match:
            answer = year_match.group(0)
            is_first = sentence.strip().startswith(answer)
            q = _build_question_lite(sentence, answer, "DATE", lang, is_first)
            if q and _is_valid_answer(answer):
                results.append({
                    "question": q, "answer": answer, "answer_type": "DATE",
                    "source_sentence": sentence, "method": "lite",
                })
                continue

        for match in _PROPER_NOUN_RE.finditer(sentence):
            answer = match.group(0)
            is_first = match.start() == 0
            if is_first:
                continue
            q = _build_question_lite(sentence, answer, "PROPN", lang, is_first)
            if q and _is_valid_answer(answer):
                results.append({
                    "question": q, "answer": answer, "answer_type": "PROPN",
                    "source_sentence": sentence, "method": "lite",
                })
                break

    return results[:max_questions]



def generate_questions_rule_based(passage: str, lang: str, max_questions: int = 3) -> list[dict]:
    """
    Génère jusqu'à `max_questions` paires (question, réponse) à partir
    d'un passage de texte. Tente d'abord spaCy (meilleure qualité) ; si
    spaCy ou le modèle de langue n'est pas installé, bascule
    automatiquement sur le mode "lite" (regex, zéro dépendance).
    """
    if _SPACY_AVAILABLE:
        try:
            results = _generate_spacy(passage, lang, max_questions)
            if results:
                return results
        except Exception:
            pass

    return _generate_lite(passage, lang, max_questions)

