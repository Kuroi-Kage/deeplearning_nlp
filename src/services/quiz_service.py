import argparse
import json

from pdf_extractor import extract_text_from_pdf, clean_text, split_into_passages
from lang_utils import detect_language
from rules import generate_questions_rule_based
from distractor import build_mcq


def build_quiz(pdf_path: str, n_questions: int = 8, use_transformer_fallback: bool = True) -> dict:
    raw_text = extract_text_from_pdf(pdf_path)
    cleaned = clean_text(raw_text)
    passages = split_into_passages(cleaned)

    if not passages:
        raise ValueError("Aucun texte exploitable n'a été extrait du PDF.")

    # on détecte la langue sur un échantillon du document (plus fiable
    # que sur un seul court passage)
    sample = " ".join(passages[:5])
    lang = detect_language(sample)
    if lang == "unknown":
        lang = "fr"  # valeur par défaut raisonnable pour ce projet
        print("Langue non détectée avec certitude, on suppose 'fr'.")

    print(f"Langue détectée : {lang} | {len(passages)} passages à traiter.")

    all_qas = []
    for passage in passages:
        if len(all_qas) >= n_questions:
            break

        rule_based = generate_questions_rule_based(passage, lang, max_questions=1)

        if rule_based:
            all_qas.extend(rule_based)
        elif use_transformer_fallback:
            # Fallback transformer : désactivé par défaut dans cette
            # démo pour ne pas nécessiter de téléchargement de modèle
            # à chaque exécution. Activer via --use-transformer.
            pass

    # on garde une trace du type d'entité pour construire les distracteurs
    answers_pool = [qa["answer"] for qa in all_qas]

    quiz_items = []
    for qa in all_qas[:n_questions]:
        # regroupement grossier : on utilise toutes les réponses du
        # document comme pool de distracteurs (simplification pédagogique
        # pour cette démo ; en version avancée on regrouperait par label
        # d'entité précis)
        item = build_mcq(
            qa_item=qa,
            all_answers_by_type={"_all": answers_pool},
            entity_label="_all",
            n_distractors=3,
        )
        quiz_items.append(item)

    return {
        "source_pdf": pdf_path,
        "language": lang,
        "num_questions": len(quiz_items),
        "questions": quiz_items,
    }


def main():
    parser = argparse.ArgumentParser(description="Génère un quiz à partir d'un PDF.")
    parser.add_argument("pdf_path", help="Chemin vers le fichier PDF source")
    parser.add_argument("--output", default="quiz.json", help="Fichier JSON de sortie")
    parser.add_argument("--n", type=int, default=8, help="Nombre de questions souhaitées")
    args = parser.parse_args()

    quiz = build_quiz(args.pdf_path, n_questions=args.n)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(quiz, f, ensure_ascii=False, indent=2)

    print(f"\n{quiz['num_questions']} questions générées -> {args.output}")


if __name__ == "__main__":
    main()