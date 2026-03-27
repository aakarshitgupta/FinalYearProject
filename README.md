# Explainable Fake News Detection with a MERN-Style Web App

This project now supports a MERN-style development setup for the final-year fake news detection system. The UI is built with React, the API is built with Express, MongoDB can store analysis history, and the existing Python BERT/LIME/SHAP pipeline remains the inference engine behind the API.

## Stack

- Frontend: React with Vite
- Backend: Node.js + Express
- Database: MongoDB (optional for history)
- ML inference: Python, PyTorch, Transformers, LIME, SHAP

## Architecture

```text
frontend (React)
    |
    v
backend (Express API)
    |
    v
scripts/api_predict.py
    |
    v
src/fake_news_xai/*
```

The backend does not reimplement the model in JavaScript. Instead, it calls a Python bridge script so the trained model and explanation code stay reusable and accurate.

## Key Features

- Single-text fake news classification
- Token-level explanation with LIME or SHAP
- Batch screening for multiple claims
- Dataset and model summary from the API
- Optional MongoDB-backed analysis history

## Project Structure

```text
.
|-- backend/
|   |-- models/
|   |-- services/
|   `-- server.js
|-- frontend/
|   |-- src/
|   `-- vite.config.js
|-- scripts/
|   `-- api_predict.py
|-- src/
|   `-- fake_news_xai/
|-- data/
|-- artifacts/
|-- app.py
`-- requirements.txt
```

## Python Setup

Create and activate the virtual environment, then install the Python dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Train the Model

Train the default model:

```powershell
python -m fake_news_xai.train --data_path data\sample_fake_news.csv --output_dir artifacts\bert_fake_news
```

Generate a larger synthetic dataset and train a larger demo model:

```powershell
python scripts\generate_synthetic_dataset.py --samples_per_class 100
python -m fake_news_xai.train --data_path data\synthetic_fake_news_large.csv --output_dir artifacts\bert_fake_news_large
```

## Backend Setup

Install backend dependencies:

```powershell
npm install --prefix backend
```

Create a backend environment file:

```powershell
Copy-Item backend\.env.example backend\.env
```

If needed, adjust:

- `PYTHON_PATH`
- `MODEL_DIR`
- `DATA_PATH`
- `MONGODB_URI`
- `CLIENT_ORIGIN`

Run the API:

```powershell
npm run dev --prefix backend
```

The API runs on `http://localhost:5000`.

## Frontend Setup

Install frontend dependencies:

```powershell
npm install --prefix frontend
```

Run the React app:

```powershell
npm run dev --prefix frontend
```

The frontend runs on `http://localhost:5173`.

## Full MERN Development Flow

Run these in separate terminals:

```powershell
npm run dev --prefix backend
```

```powershell
npm run dev --prefix frontend
```

Open:

- Frontend: `http://localhost:5173`
- Backend health check: `http://localhost:5000/api/health`

## Streamlit

The previous Streamlit app is still present in `app.py`, but the recommended path for ongoing web development is now the React + Express setup.

## Notes

- MongoDB is optional. If `MONGODB_URI` is empty, the app still works without saved history.
- SHAP is slower than LIME on CPU.
- The backend expects trained model artifacts to already exist in the configured model directory.
