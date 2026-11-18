# AgriSmart – Production Deployment & Cloud Hosting Guide

This guide details the step-by-step procedure for deploying **AgriSmart** to production cloud platforms on a 100% free-tier architecture.

---

## 1. Architecture & Deployment Topology

```
+-------------------------------------------------------------+
|                 CLIENT LAYER (BROWSER / MOBILE)             |
+-------------------------------------------------------------+
                              | HTTPS
                              v
+-------------------------------------------------------------+
|               FRONTEND HOST (VERCEL / NETLIFY)              |
| - React 19 + Vite 5 + Tailwind CSS v4                       |
| - Environment Variable: VITE_API_BASE_URL                   |
+-------------------------------------------------------------+
                              | REST JSON / Multipart
                              v
+-------------------------------------------------------------+
|               BACKEND HOST (RENDER / RAILWAY / DOCKER)      |
| - FastAPI + Uvicorn ASGI Server                             |
| - In-Memory ML Engines:                                     |
|     * Random Forest Regressor (joblib, ~52 MB)              |
|     * TensorFlow Deep Neural Network (keras, ~1.5 MB)       |
|     * PyTorch MobileNetV2 Vision (pth, ~9 MB)               |
| - Local Geospatial Database: district_coordinates.json      |
+-------------------------------------------------------------+
                 /                           \
        HTTPS   /                             \   HTTPS
               v                               v
+-------------------------------+   +-------------------------------+
|     OPEN-METEO WEATHER API    |   |     GOOGLE GEMINI 2.0 FLASH   |
| - Current Conditions & Wind   |   | - Conversational RAG Engine   |
| - 7-Day Forecast              |   | - 31-Topic Agronomic KB       |
| - ERA5 Historical Rainfall    |   +-------------------------------+
+-------------------------------+
```

---

## 2. Storage & Memory Footprint Audit

Before deploying to containerized hosts, verify the artifact dimensions:

| Component | File Path | File Size | Memory (RAM) Usage |
|---|---|---|---|
| Random Forest Model | `backend/rf_model.joblib` | ~52.3 MB | ~110 MB RAM |
| TensorFlow DNN Model | `backend/models/tf_yield_model.keras` | ~1.4 MB | ~85 MB RAM |
| PyTorch MobileNetV2 | `backend/models/disease_classifier.pth` | ~9.1 MB | ~95 MB RAM |
| District Database | `backend/data/district_coordinates.json` | ~34 KB | < 1 MB RAM |
| Base FastAPI + Dependencies | Python runtime | — | ~120 MB RAM |
| **Total Server Footprint** | **All Models Combined** | **~63 MB disk** | **~410 MB RAM** |

> [!NOTE]
> The total runtime footprint is **~410 MB RAM**, fitting comfortably within the **512 MB RAM limit** of free cloud tiers (Render, Railway Starter).

---

## 3. Backend Deployment (Render.com – Recommended Free Tier)

### Step 3.1: Create Render Web Service
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Configure the service parameters:
   - **Name**: `AgriSmart-backend`
   - **Region**: `Singapore` or `Frankfurt` (closest to your audience)
   - **Root Directory**: `CropYieldApp/CropYieldApp/backend`
   - **Environment**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: `Free` (0.1 CPU, 512 MB RAM)

### Step 3.2: Configure Environment Variables
Under the **Environment** tab, add:

| Key | Value | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.10.12` | Ensures consistent package wheel availability |
| `TF_ENABLE_ONEDNN_OPTS` | `0` | Disables verbose TensorFlow oneDNN floating-point logs |
| `TF_CPP_MIN_LOG_LEVEL` | `2` | Suppresses TensorFlow INFO/WARNING logs |
| `GEMINI_API_KEY` | `AIzaSy...` *(Your Gemini Key)* | Powers Module 3 GenAI Chatbot |

### Step 3.3: Verify Backend Live Health
Once deployment completes, visit:
`https://AgriSmart-backend.onrender.com/health`

Expected JSON response:
```json
{
  "status": "healthy",
  "app": "AgriSmart",
  "version": "2.0.0",
  "rf_model_loaded": true,
  "tf_model_loaded": true,
  "disease_model_loaded": true,
  "locations_loaded": 143
}
```

---

## 4. Frontend Deployment (Vercel – Recommended Free Tier)

### Step 4.1: Import Project to Vercel
1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New...** -> **Project**.
3. Select your GitHub repository.
4. Configure the build parameters:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `CropYieldApp/CropYieldApp/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### Step 4.2: Add Environment Variable
Under **Environment Variables**, add:

| Key | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://AgriSmart-backend.onrender.com` |

*(Replace with your actual Render backend URL without trailing slash).*

### Step 4.3: Deploy & Verify
Click **Deploy**. Within 60 seconds, your site is live at:
`https://AgriSmart.vercel.app`

---

## 5. Alternative: Containerized Docker Deployment

For self-hosting on AWS EC2, DigitalOcean Droplet, or local Docker:

### Backend `Dockerfile`
Create `CropYieldApp/CropYieldApp/backend/Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
```

Build and run:
```bash
docker build -t AgriSmart-backend:v2 ./backend
docker run -d -p 8001:8001 --env GEMINI_API_KEY="your_key" AgriSmart-backend:v2
```

---

## 6. Pre-Launch Production Verification Checklist

- [x] **Zero Hardcoded Credentials**: Checked all code files for exposed API keys.
- [x] **CORS Middleware Active**: `allow_origins=["*"]` configured in `app.py`.
- [x] **API Base URL Fallback**: Frontend dynamically uses `import.meta.env.VITE_API_BASE_URL` with local fallback `http://localhost:8001`.
- [x] **Open-Meteo Compliance**: Proper attribution rendered in SmartDashboard (`Weather data provided by Open-Meteo`).
- [x] **Model Weights Verified**: PyTorch `.pth` (12 classes), TensorFlow `.keras`, Scikit-learn `.joblib` load without errors.
- [x] **OOD Uncertainty Rejection**: Tested synthetic non-plant noise to ensure no misdiagnosis hallucination.
- [x] **Graceful Error Handling**: 400 for unknown districts, 422 for invalid payloads, 503 for missing Gemini API key.
