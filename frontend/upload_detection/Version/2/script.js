const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
let selectedFile = null;

// drag & drop
dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("bg-gray-200");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("bg-gray-200");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  selectedFile = e.dataTransfer.files[0];
  dropZone.innerText = selectedFile.name;
});

fileInput.addEventListener("change", () => {
  selectedFile = fileInput.files[0];
  dropZone.innerText = selectedFile.name;
});

document.getElementById("uploadBtn").addEventListener("click", upload);

function upload() {
  const status = document.getElementById("status");
  const progressBar = document.getElementById("progressBar");

  if (!selectedFile) {
    alert("Please select file");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "http://localhost:8000/predict/");

  xhr.responseType = "json";  // ✅ 必須放這

  xhr.upload.onprogress = function (e) {
    const percent = Math.round((e.loaded / e.total) * 100);
    progressBar.style.width = percent + "%";
    progressBar.innerText = percent + "%";
  };

  xhr.onload = function () {
    if (xhr.status === 200) {
      const res = xhr.response;

      // ✅ 顯示圖片
      document.getElementById("resultImage").src =
        "data:image/png;base64," + res.image;

      // ✅ 顯示數據
      document.getElementById("totalArea").innerText =
        res.total_area + " km²";

      document.getElementById("snowArea").innerText =
        res.snow_area + " km²";

      document.getElementById("percentage").innerText =
        res.percentage + "%";

      // ✅ 畫 chart
      renderChart(
        res.snow_area,
        res.total_area - res.snow_area
      );

      status.innerText = "Done";
    } else {
      status.innerText = "Error: " + xhr.status;
    }
  };

  xhr.send(formData);
}

// chart
function renderChart(snow, nonSnow) {
  new Chart(document.getElementById("chart"), {
    type: "doughnut",
    data: {
      labels: ["Snow", "Non-Snow"],
      datasets: [{
        data: [snow, nonSnow],
          backgroundColor: [
          "#327AAA",
          "#9DD0F0"
        ]
      }]
    }
  });
}