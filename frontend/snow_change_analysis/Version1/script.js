const leftMonthEl = document.getElementById("leftMonth");
const rightMonthEl = document.getElementById("rightMonth");
const apiBaseEl = document.getElementById("apiBase");
const compareBtn = document.getElementById("compareBtn");
const swapBtn = document.getElementById("swapBtn");
const statusPill = document.getElementById("statusPill");

const diffImage = document.getElementById("diffImage");
const placeholder = document.getElementById("previewPlaceholder");
const rawOutput = document.getElementById("rawOutput");

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

function setStatus(text, kind = "ready") {
  statusPill.textContent = text;
  if (kind === "error") {
    statusPill.style.background = "rgba(239, 68, 68, 0.10)";
    statusPill.style.color = "#dc2626";
    statusPill.style.borderColor = "rgba(239, 68, 68, 0.18)";
  } else if (kind === "busy") {
    statusPill.style.background = "rgba(22, 119, 255, 0.10)";
    statusPill.style.color = "#1d4ed8";
    statusPill.style.borderColor = "rgba(22, 119, 255, 0.18)";
  } else {
    statusPill.style.background = "rgba(22, 163, 74, 0.10)";
    statusPill.style.color = "#16a34a";
    statusPill.style.borderColor = "rgba(22, 163, 74, 0.18)";
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

function getApiBase() {
  const raw = apiBaseEl.value.trim();
  return raw ? raw.replace(/\/$/, "") : "";
}

function buildCompareUrl(left, right) {
  const base = getApiBase();
  const path = `/compare?left=${encodeURIComponent(left)}&right=${encodeURIComponent(right)}`;
  return base ? `${base}${path}` : path;
}

function setPlaceholderVisible(visible) {
  placeholder.style.display = visible ? "flex" : "none";
  diffImage.style.display = visible ? "none" : "block";
}

function resetOutput() {
  rawOutput.textContent = "{}";
  diffImage.removeAttribute("src");
  setPlaceholderVisible(true);
}

function updateMetrics(data) {
  const left = data.left || {};
  const right = data.right || {};
  const gain = data.gain || {};
  const loss = data.loss || {};
  const net = data.net || {};

  fields.leftArea.textContent = fmtKm2(left.snow_area_km2 ?? left.snow_area ?? left.area);
  fields.leftRatio.textContent = left.ratio != null ? `Coverage: ${fmtPct(left.ratio)}` : "Coverage: —";

  fields.rightArea.textContent = fmtKm2(right.snow_area_km2 ?? right.snow_area ?? right.area);
  fields.rightRatio.textContent = right.ratio != null ? `Coverage: ${fmtPct(right.ratio)}` : "Coverage: —";

  fields.gainArea.textContent = fmtKm2(gain.snow_area_km2 ?? gain.area);
  fields.gainPixels.textContent = gain.pixels != null ? fmtPixels(gain.pixels) : "—";

  fields.lossArea.textContent = fmtKm2(loss.snow_area_km2 ?? loss.area);
  fields.lossPixels.textContent = loss.pixels != null ? fmtPixels(loss.pixels) : "—";

  fields.netArea.textContent = fmtKm2(net.snow_area_km2 ?? net.area);
  fields.netNote.textContent = net.snow_area_km2 != null
    ? (Number(net.snow_area_km2) >= 0 ? "Positive change" : "Negative change")
    : "—";

  if (left.ratio != null && right.ratio != null) {
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

  setStatus("Comparing...", "busy");
  compareBtn.disabled = true;
  compareBtn.textContent = "Working...";

  const url = buildCompareUrl(left, right);

  try {
    const res = await fetch(url, {
      method: "GET",
      headers: { "Accept": "application/json" }
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    rawOutput.textContent = JSON.stringify(data, null, 2);
    updateMetrics(data);

    if (data.diff_image_url) {
      diffImage.src = data.diff_image_url;
      setPlaceholderVisible(false);
    } else {
      resetOutput();
    }

    setStatus(`Compared ${monthLabel(left)} → ${monthLabel(right)}`, "ready");
  } catch (err) {
    console.error(err);
    setStatus("API error", "error");
    rawOutput.textContent = JSON.stringify({
      error: "Failed to fetch comparison data",
      message: String(err)
    }, null, 2);
    resetOutput();
  } finally {
    compareBtn.disabled = false;
    compareBtn.textContent = "Compare";
  }
}

swapBtn.addEventListener("click", () => {
  const left = leftMonthEl.value;
  leftMonthEl.value = rightMonthEl.value;
  rightMonthEl.value = left;
});

compareBtn.addEventListener("click", compareMonths);

[leftMonthEl, rightMonthEl].forEach((el) => {
  el.addEventListener("change", () => {
    setStatus("Ready", "ready");
  });
});

// optional auto state
setPlaceholderVisible(true);
setStatus("Ready", "ready");
