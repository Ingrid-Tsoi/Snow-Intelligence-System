const uploadBtn = document.getElementById("uploadBtn");
const predictBtn = document.getElementById("predictBtn");
const fileInput = document.getElementById("fileInput");

const page1 = document.getElementById("page1");
const page2 = document.getElementById("page2");

const resultImage = document.getElementById("resultImage");
const stats = document.getElementById("stats");

let selectedFile = null;

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

  /* ===== API RESPONSE ===== */
  const formData = new FormData();
  formData.append("file", selectedFile);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "http://localhost:8000/predict/");
  xhr.responseType = "json";

  xhr.onload = function () {

    if (xhr.status === 200) {

      const res = xhr.response;

      // 轉換成統一格式
      const data = {
        image: "data:image/png;base64," + res.image,
        total: res.total_area,
        snow: res.snow_area,
        percent: res.percentage
      };

      showResult(data);   // ← 保留原本 UI flow

      status.innerText = "Done";

    } else {
      status.innerText = "Error: " + xhr.status;
    }
  };

  xhr.send(formData);
};


/* ===== SHOW RESULT PAGE ===== */
function showResult(data) {

  page1.classList.add("hidden");
  page2.classList.remove("hidden");

  resultImage.src = data.image;

  stats.innerHTML = `
    Total Area: ${data.total} km² <br>
    Snow Area: ${data.snow} km² <br>
    Percentage: ${data.percent}%
  `;

  renderChart(data);
}


/* ===== DONUT CHART ===== */
function renderChart(data) {

  const ctx = document.getElementById('chart');

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Snow', 'Non-Snow'],
      datasets: [{
        data: [data.snow, data.total - data.snow],
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


/* ===== BACK BUTTON ===== */
document.getElementById("backBtn").onclick = () => {
  page2.classList.add("hidden");
  page1.classList.remove("hidden");
};