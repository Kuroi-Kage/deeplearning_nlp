from functools import lru_cache
from transformers import pipeline

_MODEL_NAMES = {
    "en": "valhalla/t5-base-qg-hl",
    "fr": "google/mt5-small",  # fallback multilingue, qualité limitée
}


@lru_cache(maxsize=2)
def _get_pipeline(lang: str):
    model_name = _MODEL_NAMES.get(lang)
    if not model_name:
        raise ValueError(f"Pas de modèle transformer configuré pour la langue : {lang}")
    return pipeline("text2text-generation", model=model_name)


def generate_question_transformer(passage: str, answer: str, lang: str) -> str:
    """
    Génère une question à partir d'un passage et d'une réponse cible
    ("answer-aware question generation").

    Args:
        passage: le texte source
        answer: la réponse que la question générée doit cibler
        lang: 'en' ou 'fr'

    Returns:
        La question générée (chaîne de caractères)
    """
    gen = _get_pipeline(lang)

    if lang == "en":
        # Format attendu par valhalla/t5-base-qg-hl : la réponse est
        # surlignée avec des balises <hl> dans le texte.
        highlighted = passage.replace(answer, f"<hl> {answer} <hl>", 1)
        prompt = f"generate question: {highlighted}"
    else:
        # Prompt instructif pour un modèle multilingue générique
        prompt = (
            f"Génère une question en français dont la réponse est "
            f"'{answer}', à partir du texte suivant : {passage}"
        )

    output = gen(prompt, max_length=64, num_return_sequences=1)
    return output[0]["generated_text"].strip()


if __name__ == "__main__":
    
    passage_en = "Marie Curie won the Nobel Prize in Physics in 1903."
    print(generate_question_transformer(passage_en, "1903", "en"))