# Snow Intelligence System

An end-to-end machine learning system for detecting, visualising, and analysing snow coverage from satellite imagery.

The system combines a U-Net–based snow segmentation model, a FastAPI backend, and web-based geospatial visualisation tools.

## Features

* Snow detection from satellite imagery
* U-Net semantic segmentation model
* FastAPI inference backend
* Snow change analysis
* Terrain analysis
* Time slider visualisation
* Swipe comparison
* NDSI raster analysis

## Tech Stack

* **Machine Learning:** PyTorch, OpenCV
* **Backend:** Python, FastAPI
* **Frontend:** HTML, CSS, JavaScript
* **Geospatial:** ArcGIS JavaScript API
* **Data:** GeoJSON, GeoTIFF / NDSI raster data

## Project Structure

```text
Snow-Intelligence-System/
├── backend/
│   ├── data/               # GeoJSON and NDSI raster datasets
│   ├── model/              # U-Net model and trained weights
│   ├── output/analysis/    # Snow change analysis outputs
│   ├── tests/              # Backend tests
│   ├── utils/              # Processing and inference modules
│   └── main.py             # FastAPI application
│
├── frontend/
│   ├── upload_detection/   # Snow detection interface
│   ├── snow_change_analysis/
│   └── gis_app/            # GIS visualisation tools
│
└── notebooks/
    └── snow_model_training.ipynb
```

## Installation

Install the required Python dependencies:

```bash
pip install -r backend/requirements.txt
```

## Run Locally

The backend and frontend should be run in **two separate terminals**.

### Terminal 1 — Backend

```bash
cd backend
python -m uvicorn main:app --reload
```

The FastAPI backend will run at:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

### Terminal 2 — Frontend

From the project root:

```bash
cd frontend
python -m http.server 5500
```

The frontend will be available at:

```text
http://localhost:5500
```

Individual applications can then be accessed through:

```text
/upload_detection/
/snow_change_analysis/
/gis_app/
```

## Model Training

The snow segmentation model training workflow is available in:

```text
notebooks/snow_model_training.ipynb
```

The trained model is stored at:

```text
backend/model/snow.pth
```

## Model Performance

The trained snow segmentation model achieves approximately:

* **mIoU:** 0.96
* **Snow IoU:** 0.956
* **Non-snow IoU:** 0.965
* **Overall Accuracy:** 0.98

## Testing

Backend tests are located in:

```text
backend/tests/
```

Run the test suite from the backend directory:

```bash
cd backend
pytest
```

## Status

The system is a functional prototype demonstrating an end-to-end workflow from snow segmentation and backend inference to geospatial visualisation and snow change analysis.
