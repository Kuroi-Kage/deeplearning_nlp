import os
import tempfile

from flask import Flask, request, jsonify

from src.services.quiz_service import build_quiz

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/generate-quiz", methods=["OPTIONS"])
def generate_quiz_preflight():
    # Répond aux requêtes "preflight" CORS envoyées par le navigateur
    return "", 204


ALLOWED_EXTENSIONS = {"pdf"}
MAX_CONTENT_LENGTH = 20 * 1024 * 1024 
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/generate-quiz", methods=["POST"])
def generate_quiz():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu (champ 'file' manquant)."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide."}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": "Seuls les fichiers PDF sont acceptés."}), 400

    try:
        n_questions = int(request.form.get("n_questions", 8))
    except ValueError:
        n_questions = 8

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        quiz = build_quiz(tmp_path, n_questions=n_questions)
        return jsonify(quiz)

    except ValueError as e:
        
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Erreur interne lors de la génération : {e}"}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    app.run(debug=True, port=5000)