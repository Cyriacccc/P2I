
// ==================================================
// FRAME — VIDEO ASSISTANT
// Gestion de l'interface et génération du Best Of
// ==================================================


// --------------------------------------------------
// RÉCUPÉRATION DES ÉLÉMENTS HTML
// --------------------------------------------------

const input = document.getElementById("video-input");
const dropZone = document.getElementById("drop-zone");
const fileInfo = document.getElementById("file-info");
const fileName = document.getElementById("file-name");
const removeButton = document.getElementById("remove-file");
const generateButton = document.getElementById("generate-button");
const buttonLabel = document.getElementById("button-label");
const notice = document.getElementById("notice");
const result = document.getElementById("result");
const resultVideo = document.getElementById("result-video");
const downloadLink = document.getElementById("download-link");


// --------------------------------------------------
// GESTION DES RÉGLAGES
// --------------------------------------------------

const settingInputs = document.querySelectorAll(
    ".settings input[type='range']"
);

function updateSettingValue(control) {
    const output = document.getElementById(`${control.id}-value`);

    if (!output) return;

    const value = Number(control.value);

    if (control.id.includes("weight")) {
        output.textContent = value.toFixed(2);
    } else if (control.id === "max-scene-duration") {
        output.textContent = `${value.toFixed(1)} s`;
    } else {
        output.textContent = value.toFixed(1);
    }
}

// Actualiser les valeurs des réglages
settingInputs.forEach(control => {
    control.addEventListener("input", () => {
        updateSettingValue(control);
    });

    updateSettingValue(control);
});


// Valeurs par défaut des réglages
const resetSettingsButton = document.getElementById("reset-settings");

const defaultSettings = {
    "k-audio": "0.7",
    "k-video-cut": "2",
    "k-video-highlight": "0.7",
    "audio-weight": "0.3",
    "video-weight": "0.7",
    "max-scene-duration": "3"
};

// Réinitialiser les réglages
if (resetSettingsButton) {
    resetSettingsButton.addEventListener("click", () => {
        settingInputs.forEach(control => {
            if (defaultSettings[control.id] !== undefined) {
                control.value = defaultSettings[control.id];
                updateSettingValue(control);
            }
        });
    });
}


// --------------------------------------------------
// GESTION DES FICHIERS VIDÉO
// --------------------------------------------------

const allowedExtensions = [
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm"
];

let selectedFile = null;
let isProcessing = false;


// Sélectionner une vidéo
function setFile(file) {
    if (!file) return;

    const extension = "." + (file.name.split(".").pop() || "").toLowerCase();

    if (!allowedExtensions.includes(extension)) {
        notice.textContent =
            "Format non accepté. Choisis une vidéo MP4, MOV, AVI, MKV ou WEBM.";
        return;
    }

    if (file.size > 500 * 1024 * 1024) {
        notice.textContent =
            "La vidéo dépasse la limite de 500 Mo.";
        return;
    }

    selectedFile = file;

    fileName.textContent =
        `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} Mo`;

    fileInfo.hidden = false;
    generateButton.disabled = false;

    notice.textContent =
        "Vidéo prête. Tu peux lancer la génération.";

    result.hidden = true;

    resultVideo.pause();
    resultVideo.removeAttribute("src");
    resultVideo.load();

    downloadLink.removeAttribute("href");
}


// Supprimer la vidéo sélectionnée
function clearFile() {
    if (isProcessing) return;

    selectedFile = null;
    input.value = "";

    fileInfo.hidden = true;
    generateButton.disabled = true;

    notice.textContent =
        "Sélectionne une vidéo pour commencer.";

    result.hidden = true;

    resultVideo.pause();
    resultVideo.removeAttribute("src");
    resultVideo.load();

    downloadLink.removeAttribute("href");
}


// Événements de sélection
input.addEventListener("change", () => {
    setFile(input.files[0]);
});

removeButton.addEventListener("click", clearFile);


// --------------------------------------------------
// GLISSER-DÉPOSER
// --------------------------------------------------

["dragenter", "dragover"].forEach(eventName => {
    dropZone.addEventListener(eventName, event => {
        event.preventDefault();
        dropZone.classList.add("dragging");
    });
});

["dragleave", "drop"].forEach(eventName => {
    dropZone.addEventListener(eventName, event => {
        event.preventDefault();
        dropZone.classList.remove("dragging");
    });
});

dropZone.addEventListener("drop", event => {
    if (isProcessing) return;

    const file = event.dataTransfer.files[0];

    if (!file) return;

    setFile(file);
});


// --------------------------------------------------
// OUTILS POUR LES REQUÊTES HTTP
// --------------------------------------------------

async function readJsonResponse(response) {
    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error(
            `Le serveur a renvoyé une réponse invalide (HTTP ${response.status}).`
        );
    }

    if (!response.ok) {
        throw new Error(
            data.error ||
            data.message ||
            `Erreur du serveur (HTTP ${response.status}).`
        );
    }

    return data;
}


// Attendre un certain temps
function wait(milliseconds) {
    return new Promise(resolve => {
        setTimeout(resolve, milliseconds);
    });
}


// --------------------------------------------------
// GÉNÉRATION DU BEST OF EN ARRIÈRE-PLAN
// --------------------------------------------------

generateButton.addEventListener("click", async () => {

    // Éviter les doubles clics
    if (!selectedFile || isProcessing) return;

    isProcessing = true;

    generateButton.disabled = true;
    input.disabled = true;
    removeButton.disabled = true;

    buttonLabel.textContent = "ENVOI DE LA VIDÉO...";

    notice.textContent =
        "Envoi de ta vidéo au serveur...";

    result.hidden = true;

    const formData = new FormData();

    // Ajouter la vidéo
    formData.append("video", selectedFile);

    // Ajouter les réglages
    document.querySelectorAll(".settings input").forEach(control => {
        formData.append(control.name, control.value);
    });

    try {

        // ==================================================
        // ÉTAPE 1 : ENVOYER LA VIDÉO
        // ==================================================

        const response = await fetch("/api/generate", {
            method: "POST",
            body: formData
        });

        const data = await readJsonResponse(response);

        if (!data.job_id || !data.status_url) {
            throw new Error(
                "Le serveur n'a pas fourni les informations de suivi de la génération."
            );
        }

        // La vidéo est reçue et le traitement a démarré.
        buttonLabel.textContent = "ANALYSE EN COURS...";

        notice.textContent =
            "Vidéo reçue. Analyse du mouvement et du son...";


        // ==================================================
        // ÉTAPE 2 : SUIVRE L'AVANCEMENT
        // ==================================================

        let completed = false;

        while (!completed) {

            // Attendre 2,5 secondes entre les vérifications
            await wait(2500);

            const statusResponse = await fetch(data.status_url, {
                method: "GET",
                cache: "no-store"
            });

            const statusData = await readJsonResponse(statusResponse);


            // La tâche est en attente
            if (statusData.status === "queued") {

                buttonLabel.textContent = "EN ATTENTE...";

                notice.textContent =
                    statusData.message ||
                    "Ta vidéo attend le début de l'analyse.";


            // La tâche est en cours
            } else if (statusData.status === "processing") {

                buttonLabel.textContent = "ANALYSE EN COURS...";

                notice.textContent =
                    statusData.message ||
                    "Analyse du mouvement et du son, puis montage automatique. Cela peut prendre plusieurs minutes.";


            // La génération est terminée
            } else if (statusData.status === "completed") {

                if (!statusData.preview_url || !statusData.download_url) {
                    throw new Error(
                        "Le Best Of est terminé, mais les liens du résultat sont manquants."
                    );
                }

                // Charger la vidéo générée
                resultVideo.src = statusData.preview_url;

                // Ajouter le lien de téléchargement
                downloadLink.href = statusData.download_url;

                // Afficher le résultat
                result.hidden = false;

                notice.textContent =
                    "Ton Best Of est prêt. Tu peux le regarder ou le télécharger.";

                buttonLabel.textContent = "GÉNÉRATION TERMINÉE";

                result.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

                completed = true;


            // La génération a échoué
            } else if (statusData.status === "failed") {

                throw new Error(
                    statusData.message ||
                    "La génération a échoué. Consulte les logs du serveur."
                );


            // État inconnu
            } else {

                throw new Error(
                    statusData.message ||
                    "État de génération inconnu."
                );
            }
        }

    } catch (error) {

        console.error(
            "Erreur pendant la génération du Best Of :",
            error
        );

        notice.textContent =
            error.message ||
            "Une erreur est survenue. Réessaie.";

    } finally {

        // Réactiver les contrôles
        isProcessing = false;

        generateButton.disabled = !selectedFile;
        input.disabled = false;
        removeButton.disabled = false;

        buttonLabel.textContent = "GÉNÉRER MON BEST OF";
    }
});
```
```