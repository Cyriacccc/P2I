
import os
import uuid
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.utils import secure_filename

from app.analyze_video import analyze_video


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

app = Flask(__name__)

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent

UPLOAD_DIR = APP_DIR / "uploads"
OUTPUT_DIR = PROJECT_DIR / "outputs"

ALLOWED_EXTENSIONS = {
    "mp4",
    "mov",
    "avi",
    "mkv",
    "webm",
}

MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 Mo

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# OUTILS
# --------------------------------------------------

def allowed_file(filename):
    """Vérifie l'extension du fichier vidéo."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# --------------------------------------------------
# PAGE PRINCIPALE
# --------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# --------------------------------------------------
# GÉNÉRATION DU BEST OF
# --------------------------------------------------

@app.route("/api/generate", methods=["POST"])
def generate_best_of():

    if "video" not in request.files:
        return jsonify({
            "error": "Aucune vidéo n'a été envoyée."
        }), 400

    video = request.files["video"]

    if not video.filename:
        return jsonify({
            "error": "Veuillez sélectionner une vidéo."
        }), 400

    if not allowed_file(video.filename):
        return jsonify({
            "error": "Format non accepté. Utilisez MP4, MOV, AVI, MKV ou WEBM."
        }), 400

    job_id = uuid.uuid4().hex

    original_name = secure_filename(video.filename)
    extension = Path(original_name).suffix.lower()

    input_path = UPLOAD_DIR / f"{job_id}{extension}"
    output_path = OUTPUT_DIR / f"{job_id}.mp4"

    try:
        # Enregistrer la vidéo importée
        video.save(str(input_path))

        print(f"📥 Vidéo reçue : {original_name}")
        print("📊 Analyse en cours...")

        # Appeler l'algorithme existant
        artifacts_dir = OUTPUT_DIR / job_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        result = analyze_video(
            str(input_path),
            output_name=f"{job_id}.mp4",
            artifacts_dir=artifacts_dir,
        )

        # Récupérer le chemin retourné par l'algorithme
        if result:
            result_path = Path(result)

            if result_path.exists():
                output_path = result_path

        # Vérifier que le Best Of a bien été créé
        if not output_path.exists():
            return jsonify({
                "error": (
                    "L'analyse est terminée, mais le fichier Best Of "
                    "est introuvable. Vérifiez le chemin de sortie "
                    "dans app/analyze_video.py et app/export.py."
                )
            }), 500

        print(f"✅ Best Of créé : {output_path}")

        return jsonify({
            "success": True,
            "job_id": job_id,
            "preview_url": url_for(
                "preview_video",
                job_id=job_id,
            ),
            "download_url": url_for(
                "download_video",
                job_id=job_id,
            ),
            "message": "Votre Best Of est prêt !",
        })

    
    except Exception:
        app.logger.exception(
            "Erreur pendant la génération du Best Of"
        )

        return jsonify({
        "error": (
                "La génération a échoué. "
                "Veuillez réessayer avec une autre vidéo."
            )
        }), 500


    finally:
        # Supprimer la vidéo source après le traitement
        if input_path.exists():
            try:
                input_path.unlink()
            except OSError:
                app.logger.warning(
                    "Impossible de supprimer la vidéo temporaire : %s",
                    input_path,
                )


# --------------------------------------------------
# PRÉVISUALISATION DU BEST OF
# --------------------------------------------------

@app.route("/api/preview/<job_id>")
def preview_video(job_id):

    # Accepter uniquement les identifiants générés par le serveur
    if not job_id.isalnum():
        return jsonify({
            "error": "Identifiant invalide."
        }), 400

    video_path = OUTPUT_DIR / f"{job_id}.mp4"

    if not video_path.is_file():
        return jsonify({
            "error": "Vidéo introuvable."
        }), 404

    return send_file(
        video_path,
        mimetype="video/mp4",
        conditional=True,
    )


# --------------------------------------------------
# TÉLÉCHARGEMENT DU BEST OF
# --------------------------------------------------

@app.route("/api/download/<job_id>")
def download_video(job_id):

    if not job_id.isalnum():
        return jsonify({
            "error": "Identifiant invalide."
        }), 400

    video_path = OUTPUT_DIR / f"{job_id}.mp4"

    if not video_path.is_file():
        return jsonify({
            "error": "Vidéo introuvable."
        }), 404

    return send_file(
        video_path,
        mimetype="video/mp4",
        as_attachment=True,
        download_name="best_of.mp4",
    )


# --------------------------------------------------
# ERREUR : FICHIER TROP VOLUMINEUX
# --------------------------------------------------

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "La vidéo dépasse la limite autorisée de 500 Mo."
    }), 413


# --------------------------------------------------
# LANCEMENT DU SERVEUR
# --------------------------------------------------


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
    )

