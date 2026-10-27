
import os
import uuid
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, render_template, request, send_file, url_for
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

ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
MAX_UPLOAD_SIZE = 500 * 1024 * 1024

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Une seule analyse à la fois pour limiter la consommation mémoire.
executor = ThreadPoolExecutor(max_workers=1)

# Les tâches sont conservées en mémoire.
# Attention : elles sont perdues si le processus redémarre.
jobs = {}
jobs_lock = threading.Lock()


# --------------------------------------------------
# OUTILS
# --------------------------------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def update_job(job_id, **values):
    """Met à jour les informations d'une tâche de manière sécurisée."""
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(values)


# --------------------------------------------------
# TRAITEMENT VIDÉO EN ARRIÈRE-PLAN
# --------------------------------------------------

def process_video(job_id, input_path, settings):
    """Exécute l'algorithme vidéo dans un thread séparé."""

    artifacts_dir = OUTPUT_DIR / job_id
    output_path = OUTPUT_DIR / f"{job_id}.mp4"

    try:
        update_job(
            job_id,
            status="processing",
            message="Analyse du mouvement et du son...",
        )

        print(
            f"🎬 [{job_id}] Début de l'analyse vidéo",
            flush=True,
        )

        # Lancer l'algorithme existant.
        result = analyze_video(
            str(input_path),
            k_audio=settings["k_audio"],
            k_video_cut=settings["k_video_cut"],
            k_video_highlight=settings["k_video_highlight"],
            audio_weight=settings["audio_weight"],
            video_weight=settings["video_weight"],
            max_scene_duration=settings["max_scene_duration"],
            output_name=f"{job_id}.mp4",
            artifacts_dir=artifacts_dir,
            min_bestof_duration=settings["min_bestof_duration"],
            max_bestof_duration=settings["max_bestof_duration"],
        )

        print(
            f"✅ [{job_id}] Analyse terminée",
            flush=True,
        )

        # Récupérer le chemin retourné par l'algorithme.
        if result:
            result_path = Path(result)

            if result_path.is_file():
                output_path = result_path

        # Vérifier que la vidéo a réellement été créée.
        if not output_path.is_file():
            raise FileNotFoundError(
                "L'algorithme n'a pas produit le fichier Best Of attendu."
            )

        # IMPORTANT :
        # On construit directement les URL pour éviter d'appeler
        # url_for() depuis le thread d'arrière-plan.
        update_job(
            job_id,
            status="completed",
            message="Ton Best Of est prêt !",
            preview_url=f"/api/preview/{job_id}",
            download_url=f"/api/download/{job_id}",
        )

        print(
            f"🎉 [{job_id}] Best Of créé : {output_path}",
            flush=True,
        )

    except Exception as error:
        app.logger.exception(
            "[%s] Échec de la génération",
            job_id,
        )

        update_job(
            job_id,
            status="failed",
            message=(
                "La génération a échoué. "
                "Consulte les logs Render pour identifier l'erreur."
            ),
            error=str(error),
        )

    finally:
        # Supprimer la vidéo source temporaire.
        try:
            if input_path.exists():
                input_path.unlink()

        except OSError:
            app.logger.warning(
                "Impossible de supprimer la vidéo temporaire : %s",
                input_path,
            )


# --------------------------------------------------
# PAGE PRINCIPALE
# --------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# --------------------------------------------------
# DÉMARRER UNE GÉNÉRATION
# --------------------------------------------------

@app.route("/api/generate", methods=["POST"])
def generate_best_of():

    print(
        "🚀 Requête de génération reçue",
        flush=True,
    )

    # Vérifier la présence de la vidéo.
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
            "error": (
                "Format non accepté. "
                "Utilisez MP4, MOV, AVI, MKV ou WEBM."
            )
        }), 400

    # Lire les réglages envoyés par l'interface.
    try:
        settings = {
            "k_audio": float(
                request.form.get("k_audio", 0.7)
            ),
            "k_video_cut": float(
                request.form.get("k_video_cut", 2.0)
            ),
            "k_video_highlight": float(
                request.form.get("k_video_highlight", 0.7)
            ),
            "audio_weight": float(
                request.form.get("audio_weight", 0.3)
            ),
            "video_weight": float(
                request.form.get("video_weight", 0.7)
            ),
            "max_scene_duration": float(
                request.form.get("max_scene_duration", 3.0)
            ),
            "min_bestof_duration": float(
                request.form.get("min_bestof_duration", 30)
            ),
            "max_bestof_duration": float(
                request.form.get("max_bestof_duration", 60)
            ),
        }

    except (ValueError, TypeError):
        return jsonify({
            "error": "Un ou plusieurs réglages sont invalides."
        }), 400

    # Valider les réglages.
    if not 0 <= settings["k_audio"] <= 2:
        return jsonify({
            "error": "Le seuil audio doit être entre 0 et 2."
        }), 400

    if not 0.5 <= settings["k_video_cut"] <= 4:
        return jsonify({
            "error": "Le seuil de coupure doit être entre 0,5 et 4."
        }), 400

    if not 0 <= settings["k_video_highlight"] <= 2:
        return jsonify({
            "error": "Le seuil des moments forts doit être entre 0 et 2."
        }), 400

    if not (
        0 <= settings["audio_weight"] <= 1
        and 0 <= settings["video_weight"] <= 1
    ):
        return jsonify({
            "error": (
                "Les poids audio et vidéo doivent être entre 0 et 1."
            )
        }), 400

    if (
        settings["audio_weight"] + settings["video_weight"]
        <= 0
    ):
        return jsonify({
            "error": "Au moins un des deux poids doit être positif."
        }), 400

    if not 1 <= settings["max_scene_duration"] <= 10:
        return jsonify({
            "error": (
                "La durée maximale des scènes doit être entre 1 et 10 secondes."
            )
        }), 400

    if settings["min_bestof_duration"] <= 0:
        return jsonify({
            "error": "La durée minimale doit être positive."
        }), 400

    if (
        settings["max_bestof_duration"]
        < settings["min_bestof_duration"]
    ):
        return jsonify({
            "error": (
                "La durée maximale doit être supérieure "
                "ou égale à la durée minimale."
            )
        }), 400

    # Créer un identifiant unique pour cette génération.
    job_id = uuid.uuid4().hex

    original_name = secure_filename(video.filename)
    extension = Path(original_name).suffix.lower()

    input_path = UPLOAD_DIR / f"{job_id}{extension}"

    try:
        # Enregistrer la vidéo envoyée.
        video.save(str(input_path))

        print(
            f"📥 [{job_id}] Vidéo reçue : {original_name}",
            flush=True,
        )

        # Enregistrer l'état initial de la tâche.
        with jobs_lock:
            jobs[job_id] = {
                "status": "queued",
                "message": "Vidéo reçue. En attente de l'analyse...",
            }

        # Lancer le traitement en arrière-plan.
        executor.submit(
            process_video,
            job_id,
            input_path,
            settings,
        )

        print(
            f"⏳ [{job_id}] Tâche envoyée au traitement en arrière-plan",
            flush=True,
        )

        # Répondre immédiatement au navigateur.
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status_url": url_for(
                "job_status",
                job_id=job_id,
            ),
            "message": "La génération a démarré.",
        }), 202

    except Exception:
        app.logger.exception(
            "Impossible de démarrer la génération"
        )

        # Nettoyer la vidéo en cas d'erreur au démarrage.
        try:
            if input_path.exists():
                input_path.unlink()

        except OSError:
            app.logger.warning(
                "Impossible de supprimer le fichier : %s",
                input_path,
            )

        with jobs_lock:
            jobs.pop(job_id, None)

        return jsonify({
            "error": "Impossible de démarrer la génération."
        }), 500


# --------------------------------------------------
# SUIVRE L'AVANCEMENT
# --------------------------------------------------

@app.route("/api/status/<job_id>", methods=["GET"])
def job_status(job_id):

    if not job_id.isalnum():
        return jsonify({
            "error": "Identifiant invalide."
        }), 400

    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return jsonify({
                "status": "unknown",
                "message": (
                    "Tâche introuvable. "
                    "Le serveur a peut-être redémarré."
                ),
            }), 404

        result = dict(job)

    return jsonify(result), 200


# --------------------------------------------------
# PRÉVISUALISATION
# --------------------------------------------------

@app.route("/api/preview/<job_id>", methods=["GET"])
def preview_video(job_id):

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
# TÉLÉCHARGEMENT
# --------------------------------------------------

@app.route("/api/download/<job_id>", methods=["GET"])
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
        conditional=True,
    )


# --------------------------------------------------
# GESTION DES ERREURS
# --------------------------------------------------

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "La vidéo dépasse la limite autorisée de 500 Mo."
    }), 413


# --------------------------------------------------
# LANCEMENT LOCAL
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
    )