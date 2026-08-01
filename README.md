# Quiz Generator — Backend (API Flask)

API qui génère automatiquement un quiz à choix multiples à partir d'un document PDF, en français ou en anglais.

**Interface associée :** [Interface-quiz](https://github.com/Kuroi-Kage/Interface-quiz) (React) — ce backend seul n'a pas d'interface, il expose une API REST.

## Stack

- Flask (API REST)
- pdfplumber (extraction du texte PDF)
- spaCy / langdetect (détection de langue et d'entités)
- Génération de questions par règles linguistiques (fallback transformer T5 prévu, non encore branché)

## Installation

```bash
pip install -r requirements.txt --break-system-packages
python -m spacy download fr_core_news_sm
python -m spacy download en_core_web_sm
```

## Lancer le serveur

```bash
python app.py
```

Le serveur démarre sur `http://localhost:5000`.

## Endpoints

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/health` | Vérifie que l'API répond |
| POST | `/api/generate-quiz` | Génère un quiz. Champs : `file` (PDF), `n_questions` (optionnel, défaut 8) |

### Exemple

```bash
curl -F "file=@mon_document.pdf" -F "n_questions=5" http://localhost:5000/api/generate-quiz
```


