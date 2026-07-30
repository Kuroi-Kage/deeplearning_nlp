import random


def build_distractors(correct_answer: str, same_type_answers: list[str], n: int = 3) -> list[str]:
    """
    Construit une liste de distracteurs pour une réponse donnée.

    Args:
        correct_answer: la bonne réponse à exclure du pool
        same_type_answers: pool de réponses du même type d'entité
                            (ex: toutes les dates du document)
        n: nombre de distracteurs souhaités

    Returns:
        Liste de distracteurs (peut être plus courte que n si le pool
        est insuffisant)
    """
    pool = [a for a in set(same_type_answers) if a != correct_answer]
    random.shuffle(pool)
    return pool[:n]


def build_mcq(qa_item: dict, all_answers_by_type: dict, entity_label: str, n_distractors: int = 3) -> dict:
    """
    Transforme un item {"question", "answer", ...} en QCM complet.

    Args:
        qa_item: dict contenant au moins "question" et "answer"
        all_answers_by_type: dict {label_entité: [réponses...]} construit
                              sur l'ensemble du document
        entity_label: le type d'entité de la réponse (pour piocher le bon pool)
        n_distractors: nombre de mauvaises réponses à générer

    Returns:
        Le qa_item enrichi d'un champ "choices" (liste mélangée incluant
        la bonne réponse) et "correct_index"
    """
    pool = all_answers_by_type.get(entity_label, [])
    distractors = build_distractors(qa_item["answer"], pool, n=n_distractors)

    choices = distractors + [qa_item["answer"]]
    random.shuffle(choices)

    qa_item["choices"] = choices
    qa_item["correct_index"] = choices.index(qa_item["answer"])
    return qa_item