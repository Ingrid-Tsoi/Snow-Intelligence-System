const leftMonthEl = document.getElementById("leftMonth");
const rightMonthEl = document.getElementById("rightMonth");
const compareBtn = document.getElementById("compareBtn");
const swapBtn = document.getElementById("swapBtn");
const statusPill = document.getElementById("statusPill");

const diffImage = document.getElementById("diffImage");
const placeholder = document.getElementById("previewPlaceholder");
const fields = {
  leftArea: document.getElementById("leftArea"),
  leftRatio: document.getElementById("leftRatio"),
  rightArea: document.getElementById("rightArea"),
  rightRatio: document.getElementById("rightRatio"),
  gainArea: document.getElementById("gainArea"),
  gainPixels: document.getElementById("gainPixels"),
  lossArea: document.getElementById("lossArea"),
  lossPixels: document.getElementById("lossPixels"),
  netArea: document.getElementById("netArea"),
  netNote: document.getElementById("netNote"),
  coverageDelta: document.getElementById("coverageDelta"),
  coverageNote: document.getElementById("coverageNote"),
};

const API_BASE = "http://127.0.0.1:8000";

function setStatus(text, kind = "ready") {
  statusPill.textContent = text;
  if (kind === "error") {
    statusPill.style.background = "rgba(231, 76, 60, 0.12)";
    statusPill.style.borderColor = "rgba(231, 76, 60, 0.22)";
    statusPill.style.color = "#b42318";
  } else if (kind === "busy") {
    statusPill.style.background = "rgba(50, 122, 170, 0.14)";
    statusPill.style.borderColor = "rgba(50, 122, 170, 0.22)";
    statusPill.style.color = "#fff";
  } else {
    statusPill.style.background = "rgba(255,255,255,0.18)";
    statusPill.style.borderColor = "rgba(255,255,255,0.24)";
    statusPill.style.color = "#fff";
  }
}

function fmtKm2(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toFixed(2)} km²`;
}

function fmtPct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toFixed(2)}%`;
}

function fmtPixels(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toLocaleString()} px`;
}

function monthLabel(yyyymm) {
  if (!yyyymm || yyyymm.length !== 6) return yyyymm || "—";
  return `${yyyymm.slice(0, 4)}-${yyyymm.slice(4, 6)}`;
}

function setPreviewVisible(visible) {
  placeholder.style.display = visible ? "flex" : "none";
  diffImage.style.display = visible ? "none" : "block";
}

function resetPreview() {
  diffImage.removeAttribute("src");
  setPreviewVisible(true);
}

function normalizeImage(data) {
  if (data.diff_image_base64) return `data:image/png;base64,${data.diff_image_base64}`;
  if (data.diff_image_url) return data.diff_image_url;
  if (data.diff_image_path) return data.diff_image_path;
  return null;
}

function updateMetrics(data) {
  const left = data.left || {};
  const right = data.right || {};
  const gain = data.gain || {};
  const loss = data.loss || {};
  const net = data.net || {};

  fields.leftArea.textContent = fmtKm2(left.snow_area_km2);
  fields.leftRatio.textContent = left.ratio != null ? `Coverage: ${fmtPct(left.ratio)}` : "Coverage: —";

  fields.rightArea.textContent = fmtKm2(right.snow_area_km2);
  fields.rightRatio.textContent = right.ratio != null ? `Coverage: ${fmtPct(right.ratio)}` : "Coverage: —";

  fields.gainArea.textContent = fmtKm2(gain.snow_area_km2);
  fields.gainPixels.textContent = gain.pixels != null ? fmtPixels(gain.pixels) : "—";

  fields.lossArea.textContent = fmtKm2(loss.snow_area_km2);
  fields.lossPixels.textContent = loss.pixels != null ? fmtPixels(loss.pixels) : "—";

  fields.netArea.textContent = fmtKm2(net.snow_area_km2);
  fields.netNote.textContent = net.snow_area_km2 != null
    ? (Number(net.snow_area_km2) >= 0 ? "Positive change" : "Negative change")
    : "—";

  if (data.coverage_delta_pct !== null && data.coverage_delta_pct !== undefined && !Number.isNaN(Number(data.coverage_delta_pct))) {
    const delta = Number(data.coverage_delta_pct);
    fields.coverageDelta.textContent = `${delta >= 0 ? "+" : ""}${delta.toFixed(2)} pts`;
    fields.coverageNote.textContent = delta >= 0 ? "Coverage increased" : "Coverage decreased";
  } else if (left.ratio != null && right.ratio != null) {
    const delta = Number(right.ratio) - Number(left.ratio);
    fields.coverageDelta.textContent = `${delta >= 0 ? "+" : ""}${delta.toFixed(2)} pts`;
    fields.coverageNote.textContent = delta >= 0 ? "Coverage increased" : "Coverage decreased";
  } else {
    fields.coverageDelta.textContent = "—";
    fields.coverageNote.textContent = "Coverage change unavailable";
  }
}

async function compareMonths() {
  const left = leftMonthEl.value;
  const right = rightMonthEl.value;

  if (!left || !right) {
    setStatus("Missing months", "error");
    return;
  }

  if (left === right) {
    setStatus("Choose two different months", "error");
    return;
  }

  compareBtn.disabled = true;
  compareBtn.textContent = "Working...";
  setStatus("Comparing...", "busy");

  const url = `${API_BASE}/compare?left=${encodeURIComponent(left)}&right=${encodeURIComponent(right)}`;

  try {
    const res = await fetch(url, {
      method: "GET",
      headers: { "Accept": "application/json" }
    });

    const payload = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(payload.detail || `HTTP ${res.status}`);
    }

    updateMetrics(payload);

    const imageUrl = normalizeImage(payload);
    if (imageUrl) {
      diffImage.src = imageUrl;
      setPreviewVisible(false);
    } else {
      resetPreview();
    }

    setStatus(`Compared ${monthLabel(left)} → ${monthLabel(right)}`, "ready");
  } catch (err) {
    console.error(err);
    setStatus("API error", "error");
    resetPreview();
  } finally {
    compareBtn.disabled = false;
    compareBtn.textContent = "Compare";
  }
}

swapBtn.addEventListener("click", () => {
  const left = leftMonthEl.value;
  leftMonthEl.value = rightMonthEl.value;
  rightMonthEl.value = left;
  setStatus("Ready", "ready");
});

compareBtn.addEventListener("click", compareMonths);

[leftMonthEl, rightMonthEl].forEach((el) => {
  el.addEventListener("change", () => setStatus("Ready", "ready"));
});

setPreviewVisible(true);
setStatus("Ready", "ready");
