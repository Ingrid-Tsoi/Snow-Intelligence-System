document.getElementById("uploadBtn").addEventListener("click", upload);

async function upload() {
  const status = document.getElementById("status");
  status.innerText = "Uploading...";

  const file = document.getElementById("fileInput").files[0];
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("http://localhost:8000/predict/", {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error(await res.text());

    const blob = await res.blob();
    document.getElementById("resultImage").src = URL.createObjectURL(blob);

    status.innerText = "Done";
  } catch (e) {
    status.innerText = "Error: " + e.message;
  }
}