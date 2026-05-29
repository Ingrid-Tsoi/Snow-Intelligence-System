# Snow Intelligence System

## Overview

Snow Intelligence System is an end-to-end machine learning platform for detecting and analysing snow coverage from satellite imagery.

The system integrates deep learning–based semantic segmentation with backend services and web-based geospatial visualisation tools, demonstrating a full production-style pipeline from model training to deployment and user interaction.

---

## Highlights

- End-to-end ML pipeline (training → inference → visualisation)
- U-Net–based semantic segmentation for snow detection
- Production-style backend using FastAPI
- Interactive geospatial analysis using ArcGIS JavaScript API

---

## Key Features

- Upload satellite imagery for automated snow detection  
- Deep learning inference using a trained U-Net model  
- Modular pipeline: preprocessing → inference → postprocessing  
- Web interface for real-time prediction and visualisation  
- Geospatial analysis tools:
  - Terrain analysis  
  - Time-based exploration (time slider)  
  - Swipe comparison  
  - Snow change analysis  

---

## System Architecture

The system is structured into three main components:

* **Application (`upload_detection/`)**

  * Backend API for model inference and data processing
  * Frontend interface for user interaction

* **Model Training (`notebooks/`)**

  * Model training and experimentation workflow
  * Includes preprocessing, training, and evaluation

* **Visualisation Tools (`gis_app/`)**

  * Standalone web applications for spatial and temporal analysis

---

## Tech Stack

* **Backend:** Python
* **Machine Learning:** PyTorch, OpenCV
* **Frontend:** HTML, CSS, JavaScript
* **Geospatial:** ArcGIS JavaScript API
* **Data Processing:** Custom Python pipelines

---

## Project Structure

```
Snow-Intelligence-System/
├── upload_detection/   # Main application (backend + frontend)
├── notebooks/          # Model training and experiments
├── gis_app/            # Geospatial visualisation tools
```

---

## Model Training

The training pipeline is documented in:


* `notebooks/snow_model_training.ipynb`


This includes:

* Data preprocessing
* Model training (U-Net)
* Evaluation and validation

---

## Model Performance

The trained model achieves strong performance on the test dataset:

- **mIoU:** ~0.96  
- **Snow IoU:** ~0.956  
- **Non-snow IoU:** ~0.965  
- **Overall Accuracy:** ~0.98  

Training converges to a final loss of ~0.004, indicating stable optimisation.

---

## Setup

Start the FastAPI server:

```bash
pip install -r backend/requirements.txt
```

## Run Locally

```bash
python -m uvicorn main:app --reload
```

Access API docs:  
http://localhost:8000/docs


## Web Applications

The system includes geospatial web tools for analysing snow coverage outputs.

### Capabilities

- **Model Integration (`upload_detection`)**  
  Web-based interface for uploading satellite imagery and performing real-time snow segmentation using the deployed U-Net model.

- **Terrain Analysis  (`gis_app`)**  
  Visualisation tools for examining snow distribution in relation to terrain features.

- **Interactive Map Exploration**  
  Map-based interface for exploring spatial patterns in snow coverage data.

## Development Status

These applications are functional at the prototype level and demonstrate core system capabilities, including model inference integration and geospatial visualisation.

### Ongoing Work

- Enhancing UI/UX for improved usability  
- Optimising performance for larger geospatial datasets  
- Expanding analytical features (e.g. temporal comparison, change detection)  
- Improving integration between standalone tools and the main application

### Use Cases

- Snow coverage monitoring  
- Environmental and climate analysis  
- Hydrological modelling support  

## Notes

- API served via FastAPI + Uvicorn  
- Interactive documentation available at `/docs`  
- Frontend provided via static web interface  

## Project Status

The system is functionally complete for end-to-end snow detection and analysis.

Current work focuses on improving usability, scalability, and expanding analytical capabilities.
"# Snow-Intelligence-System" 
