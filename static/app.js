/**
 * Smart Waste Assistant - frontend logic.
 *
 * Camera is OFF by default on both tabs. The user explicitly starts it
 * with the "Start Camera" button and can stop it with the same button
 * (it toggles) - nothing streams from the camera until they choose to.
 * report.js (loaded before this file) provides reportToGHMC().
 */

// ---------- Tab switching ----------

const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabButtons.forEach((b) => b.classList.remove("active"));
    tabPanels.forEach((p) => p.classList.remove("active"));

    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");

    // Stop whichever camera was running when switching tabs - the user
    // has to explicitly start the camera on the new tab too.
    stopCamera(scanState);
    stopCamera(reportState);
  });
});

// ---------- Camera helpers (manual on/off, shared by both tabs) ----------

function makeCameraController({ video, toggleBtn, captureBtn, offMsg }) {
  return { video, toggleBtn, captureBtn, offMsg, stream: null };
}

async function startCamera(state) {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    state.stream = stream;
    state.video.srcObject = stream;
    state.offMsg.hidden = true;
    state.toggleBtn.textContent = "⏹️ Stop Camera";
    state.captureBtn.disabled = false;
  } catch (err) {
    alert("Could not access the camera: " + err.message);
  }
}

function stopCamera(state) {
  if (state.stream) {
    state.stream.getTracks().forEach((track) => track.stop());
    state.stream = null;
  }
  state.video.srcObject = null;
  state.offMsg.hidden = false;
  state.toggleBtn.textContent = "▶️ Start Camera";
  state.captureBtn.disabled = true;
}

function toggleCamera(state) {
  if (state.stream) {
    stopCamera(state);
  } else {
    startCamera(state);
  }
}

function captureFrame(videoEl, canvasEl) {

  if (videoEl.readyState < 2) {
    throw new Error("Camera isn't ready yet - wait a moment and try again.");
  }
  canvasEl.width = videoEl.videoWidth || 640;
  canvasEl.height = videoEl.videoHeight || 480;
  const ctx = canvasEl.getContext("2d");
  ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);
  return new Promise((resolve) => canvasEl.toBlob(resolve, "image/jpeg", 0.9));
}

// ---------- Scan Item tab ----------

const scanState = makeCameraController({
  video: document.getElementById("scan-video"),
  toggleBtn: document.getElementById("scan-camera-toggle"),
  captureBtn: document.getElementById("scan-capture-btn"),
  offMsg: document.getElementById("scan-camera-off-msg"),
});

const scanCanvas = document.getElementById("scan-canvas");
const scanResult = document.getElementById("scan-result");
const scanCategory = document.getElementById("scan-category");
const scanSubCategory = document.getElementById("scan-sub-category");
const scanBin = document.getElementById("scan-bin");
const scanDescription = document.getElementById("scan-description");
const scanSeparationsWrap = document.getElementById("scan-separations-wrap");
const scanSeparations = document.getElementById("scan-separations");
const scanImpactPositive = document.getElementById("scan-impact-positive");
const scanImpactNegative = document.getElementById("scan-impact-negative");
const scanImpactPositiveLabel = document.getElementById("scan-impact-positive-label");
const scanImpactNegativeLabel = document.getElementById("scan-impact-negative-label");
const scanExplanation = document.getElementById("scan-explanation");
const scanConfidence = document.getElementById("scan-confidence");
const scanError = document.getElementById("scan-error");

scanState.toggleBtn.addEventListener("click", () => toggleCamera(scanState));

document.getElementById("scan-capture-btn").addEventListener("click", async () => {
  const captureBtn = scanState.captureBtn;
  scanResult.hidden = true;
  scanError.hidden = true;
  captureBtn.disabled = true;
  const originalLabel = captureBtn.textContent;
  captureBtn.textContent = "Classifying…";

  try {
    const blob = await captureFrame(scanState.video, scanCanvas);
    const formData = new FormData();
    formData.append("image", blob, "item.jpg");
    const res = await fetch("/api/scan-item", { method: "POST", body: formData, cache: "no-store" });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Classification failed");

    scanCategory.textContent = `Category: ${data.category}`;
    scanSubCategory.textContent = data.sub_category ? `Identified as: ${data.sub_category}` : "";
    scanSubCategory.hidden = !data.sub_category;

    scanBin.textContent = data.bin;
    scanDescription.textContent = data.description;

    scanSeparations.innerHTML = "";
    if (data.separations && data.separations.length) {
      data.separations.forEach((step) => {
        const li = document.createElement("li");
        li.textContent = step;
        scanSeparations.appendChild(li);
      });
      scanSeparationsWrap.hidden = false;
    } else {
      scanSeparationsWrap.hidden = true;
    }

    scanImpactPositive.style.width = `${data.positive_impact_percent}%`;
    scanImpactNegative.style.width = `${data.negative_impact_percent}%`;
    scanImpactPositiveLabel.textContent = `Helps: ${data.positive_impact_percent}%`;
    scanImpactNegativeLabel.textContent = `Harms if mishandled: ${data.negative_impact_percent}%`;

    scanExplanation.textContent = data.explanation;

    scanConfidence.textContent = data.category === "unknown"
      ? "No reliable match. Retake a clear photo of one item, or check local disposal guidance."
      : `Confidence: ${(data.confidence * 100).toFixed(0)}%` +
        (data.source === "heuristic" ? " — AI model unavailable" : "");

    scanResult.hidden = false;
  } catch (err) {
    scanError.textContent = err.message;
    scanError.hidden = false;
  } finally {
    captureBtn.disabled = false;
    captureBtn.textContent = originalLabel;
  }
});

// ---------- Report Bin tab ----------

const reportState = makeCameraController({
  video: document.getElementById("report-video"),
  toggleBtn: document.getElementById("report-camera-toggle"),
  captureBtn: document.getElementById("report-capture-btn"),
  offMsg: document.getElementById("report-camera-off-msg"),
});

const reportCanvas = document.getElementById("report-canvas");
const reportResult = document.getElementById("report-result");
const reportStateEl = document.getElementById("report-state");
const reportConfidence = document.getElementById("report-confidence");
const reportError = document.getElementById("report-error");
const downloadPhotoLink = document.getElementById("download-photo-link");
const ghmcReportBtn = document.getElementById("ghmc-report-btn");

reportState.toggleBtn.addEventListener("click", () => toggleCamera(reportState));

document.getElementById("report-capture-btn").addEventListener("click", async () => {
  const captureBtn = reportState.captureBtn;
  reportResult.hidden = true;
  reportError.hidden = true;
  downloadPhotoLink.hidden = true;
  ghmcReportBtn.hidden = true;
  captureBtn.disabled = true;
  const originalLabel = captureBtn.textContent;
  captureBtn.textContent = "Checking…";

  try {
    const blob = await captureFrame(reportState.video, reportCanvas);
    const formData = new FormData();
    formData.append("image", blob, "bin.jpg");
    const res = await fetch("/api/check-bin", { method: "POST", body: formData, cache: "no-store" });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Check failed");

    reportStateEl.textContent = `Status: ${data.state}`;
    reportConfidence.textContent = `Confidence: ${(data.confidence * 100).toFixed(0)}%` +
      (data.source === "heuristic" ? " — placeholder heuristic active, install torch + transformers for accurate results" : "");
    reportResult.hidden = false;

    if (data.state === "overflowing" || data.state === "moderate") {
      downloadPhotoLink.href = URL.createObjectURL(blob);
      downloadPhotoLink.hidden = false;

      ghmcReportBtn.hidden = false;
      ghmcReportBtn.onclick = () => reportToGHMC(data.state === "overflowing" ? "overflowing bin" : "littering / partially full bin");
    }
  } catch (err) {
    reportError.textContent = err.message;
    reportError.hidden = false;
  } finally {
    captureBtn.disabled = false;
    captureBtn.textContent = originalLabel;
  }
});
