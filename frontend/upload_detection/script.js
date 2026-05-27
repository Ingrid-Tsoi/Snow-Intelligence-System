const uploadBtn = document.getElementById("uploadBtn");
const predictBtn = document.getElementById("predictBtn");
const fileInput = document.getElementById("fileInput");

const page1 = document.getElementById("page1");
const page2 = document.getElementById("page2");

const resultImage = document.getElementById("resultImage");
const status = document.getElementById("status");

const navbar = document.querySelector(".navbar");
const nav = document.querySelector(".nav");
const logo = document.getElementById("logo");

let selectedFile = null;

/* ===== HOVER PANEL & dropdown 時 → nav 黑字===== */
logo.addEventListener("click", () => {
  page1.classList.remove("hidden");
  page2.classList.add("hidden");
  document.body.classList.remove("page2");

  status.innerText = "";
  fileInput.value = "";
  selectedFile = null;
  predictBtn.disabled = true;
  resultImage.src = "";

  logo.src = "static/logo-white.svg";
  nav.classList.remove("open");
});

nav.addEventListener("mouseenter", () => {
  nav.classList.add("open");
  logo.src = "static/logo-black.svg";
});

nav.addEventListener("mouseleave", () => {
  nav.classList.remove("open");
  logo.src = document.body.classList.contains("page2")
    ? "static/logo-black.svg"
    : "static/logo-white.svg";
});

/* ===== menu links ===== */
document.querySelectorAll(".menu-link").forEach(item => {
  item.addEventListener("click", () => {
    const page = item.dataset.page;

    if (page === "terrain") {
      window.open("../gis_app/terrain_analysis.html", "_blank");
      return;
    }

    if (page === "swipe") {
      window.open("../gis_app/swipe_comparison.html", "_blank");
      return;
    }

    if (page === "time") {
      window.open("../gis_app/time_slider.html", "_blank");
      return;
    }

    if (page === "analysis") {
      window.open("http://127.0.0.1:5500/snow_change_analysis/", "_blank");
      return;
    }
  });
});

/* ===== Upload ===== */
uploadBtn.onclick = () => {
  fileInput.click();
};

fileInput.onchange = () => {
  selectedFile = fileInput.files[0];
  predictBtn.disabled = false;
};

/* ===== Predict ===== */
predictBtn.onclick = () => {
  if (!selectedFile) return;

  document.getElementById("status").innerText = "Processing...";

  const formData = new FormData();
  formData.append("file", selectedFile);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "http://localhost:8000/predict/");
  xhr.responseType = "json";

  xhr.onload = function () {
    if (xhr.status === 200) {
      const res = xhr.response;

      const data = {
        image: "data:image/png;base64," + res.image,
        total: res.total_area,
        snow: res.snow_area,
        percent: res.percentage
      };

      showResult(data);
      status.innerText = "Done";
    } else {
      status.innerText = "Error: " + xhr.status;
    }
  };

  xhr.send(formData);
};

/* ===== SHOW RESULT PAGE ===== */
function showResult(data) {
  document.getElementById("page1").classList.add("hidden");
  document.getElementById("page2").classList.remove("hidden");

  document.body.classList.add("page2");
  document.getElementById("logo").src = "static/logo-black.svg";

  document.getElementById("resultImage").src = data.image;

  document.getElementById("snow").innerText = "Snow: " + data.snow + " km²";
  document.getElementById("nonSnow").innerText = "Non-Snow: " + (data.total - data.snow) + " km²";
  document.getElementById("total").innerText = "Total: " + data.total + " km²";
  document.getElementById("percent").innerText = "Percentage: " + data.percent + "%";

  renderChart(data);
}

/* ===== DONUT CHART ===== */
let chart;
function renderChart(data) {
  const ctx = document.getElementById('chart');
  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Snow', 'Non-Snow'],
      datasets: [{
        data: [data.snow, data.total - data.snow],
        backgroundColor: ['#9DD0F0', '#2E8CC0'],
        borderWidth: 0
      }]
    },
    options: {
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });
}
