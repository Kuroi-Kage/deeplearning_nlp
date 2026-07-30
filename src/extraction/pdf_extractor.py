import re
import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrait le texte brut de toutes les pages d'un PDF."""
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)


def clean_text(raw_text: str) -> str:
    """Nettoie le texte extrait (espaces, sauts de ligne, numéros de page)."""
    text = raw_text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\b\d{1,3}\b(?=\s*$)", "", text)
    return text.strip()


def split_into_passages(text: str, min_words: int = 15, max_words: int = 60) -> list[str]:
    """
    Découpe le texte en passages de taille raisonnable pour la génération
    de questions : regroupe des phrases jusqu'à atteindre une taille cible.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)

    passages = []
    current, current_word_count = [], 0

    for sentence in sentences:
        word_count = len(sentence.split())
        if word_count == 0:
            continue
        current.append(sentence)
        current_word_count += word_count
        if current_word_count >= min_words:
            passages.append(" ".join(current))
            current, current_word_count = [], 0

    if current and current_word_count >= 5:
        passages.append(" ".join(current))

    final_passages = []
    for p in passages:
        words = p.split()
        if len(words) <= max_words:
            final_passages.append(p)
        else:
            for i in range(0, len(words), max_words):
                final_passages.append(" ".join(words[i:i + max_words]))

    return final_passages


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <chemin_du_pdf>")
        sys.exit(1)

    raw = extract_text_from_pdf(sys.argv[1])
    cleaned = clean_text(raw)
    passages = split_into_passages(cleaned)

    print(f"{len(passages)} passages extraits.\n")
    for i, p in enumerate(passages[:5], start=1):
        print(f"[{i}] {p}\n")