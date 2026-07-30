import re

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False


_FR_STOPWORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "est",
    "à", "en", "il", "elle", "ce", "que", "qui", "pour", "dans", "sur",
    "avec", "son", "sa", "ses", "au", "aux", "par", "ne", "pas", "plus",
}
_EN_STOPWORDS = {
    "the", "a", "an", "and", "is", "of", "to", "in", "he", "she",
    "it", "that", "for", "with", "his", "her", "on", "was", "were",
    "at", "by", "as", "this", "which", "are", "be",
}


def _detect_language_lite(text: str) -> str:
    words = re.findall(r"[a-zàâäéèêëïîôöùûüç]+", text.lower())
    if not words:
        return "unknown"

    fr_score = sum(1 for w in words if w in _FR_STOPWORDS)
    en_score = sum(1 for w in words if w in _EN_STOPWORDS)

    if fr_score == 0 and en_score == 0:
        return "unknown"
    return "fr" if fr_score >= en_score else "en"


def detect_language(text: str) -> str:
    """Retourne 'fr', 'en' ou 'unknown'."""
    if _LANGDETECT_AVAILABLE:
        try:
            lang = detect(text)
            if lang in ("fr", "en"):
                return lang
        except Exception:
            pass

    return _detect_language_lite(text)