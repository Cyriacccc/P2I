
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

// Afficher la valeur actuelle de chaque réglage
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

settingInputs.forEach((control) => {
  control.addEventListener("input", () => {
    updateSettingValue(control);
  });

  updateSettingValue(control);
});

// Réinitialiser tous les réglages
const resetSettingsButton = document.getElementById("reset-settings");

const defaultSettings = {
  "k-audio": "0.7",
  "k-video-cut": "2",
  "k-video-highlight": "0.7",
  "audio-weight": "0.3",
  "video-weight": "0.7",
  "max-scene-duration": "3",
};

resetSettingsButton.addEventListener("click", () => {
  settingInputs.forEach((control) => {
    control.value = defaultSettings[control.id];
    updateSettingValue(control);
  });
});

const allowedExtensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"];
let selectedFile = null;
let isProcessing = false;

function setFile(file) {
  if (!file) return;

  const extension = "." + (file.name.split(".").pop() || "").toLowerCase();

  if (!allowedExtensions.includes(extension)) {
    notice.textContent = "Format non accepté. Choisis une vidéo MP4, MOV, AVI, MKV ou WEBM.";
    return;
  }

  // Limite cohérente avec celle du serveur Flask.
  if (file.size > 500 * 1024 * 1024) {
    notice.textContent = "La vidéo dépasse la limite de 500 Mo.";
    return;
  }

  selectedFile = file;
  fileName.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} Mo`;
  fileInfo.hidden = false;
  generateButton.disabled = false;
  notice.textContent = "Vidéo prête. Tu peux lancer la génération.";
  result.hidden = true;
  resultVideo.pause();
  resultVideo.removeAttribute("src");
  resultVideo.load();
}

function clearFile() {
  selectedFile = null;
  input.value = "";
  fileInfo.hidden = true;
  generateButton.disabled = true;
  notice.textContent = "Sélectionne une vidéo pour commencer.";
}

input.addEventListener("change", () => setFile(input.files[0]));
removeButton.addEventListener("click", clearFile);

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
});

dropZone.addEventListener("drop", (event) => {
  setFile(event.dataTransfer.files[0]);
});

generateButton.addEventListener("click", async () => {
  if (!selectedFile || isProcessing) return;

  isProcessing = true;
  generateButton.disabled = true;
  input.disabled = true;
  removeButton.disabled = true;
  buttonLabel.textContent = "ANALYSE EN COURS...";
  notice.textContent = "Analyse du mouvement et du son, puis montage automatique. Cela peut prendre plusieurs minutes.";
  result.hidden = true;

 const formData = new FormData();
formData.append("video", selectedFile);

document.querySelectorAll(".settings input").forEach((input) => {
  formData.append(input.name, input.value);
});

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Impossible de générer le Best Of.");
    }

    resultVideo.src = data.preview_url;
    downloadLink.href = data.download_url;
    result.hidden = false;
    notice.textContent = "Ton Best Of est prêt. Tu peux le regarder ou le télécharger.";
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    notice.textContent = error.message || "Une erreur est survenue. Réessaie.";
  } finally {
    isProcessing = false;
    generateButton.disabled = !selectedFile;
    input.disabled = false;
    removeButton.disabled = false;
    buttonLabel.textContent = "GÉNÉRER MON BEST OF";
  }
});
