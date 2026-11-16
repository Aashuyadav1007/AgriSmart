# AgriMind AI – UI Screenshots & Visual Presentation Guide

This guide details the standard screenshot catalog for **AgriMind AI** project reports, presentations, and viva defense demonstrations.

---

## 1. Designated Screenshot Catalog

All presentation screenshots are stored in [`documentation/screenshots/`](file:///documentation/screenshots/) following this naming convention:

| ID | Filename | Target View | Recommended Resolution | Visual Highlights to Capture |
|---|---|---|---|---|
| **01** | `01_overview_dashboard.png` | **Executive Overview** | 1920 × 1080 | Live backend telemetry badge (`Connected 8001`), quick stats KPI cards (Models Loaded, Disease Classes, Supported Districts), system architecture overview, quick-action navigation cards. |
| **02** | `02_yield_predictor.png` | **Crop Yield Prediction** | 1920 × 1080 | Dual ML consensus comparison card (Random Forest vs TensorFlow DNN), agreement meter (e.g., 97.2%), multi-unit conversion badges (kg/ha, tonnes/ha, kg/Acre, kg/Bigha), input parameters form. |
| **03** | `03_disease_detector_cotton.png` | **Plant Disease Vision** | 1920 × 1080 | Uploaded Cotton leaf image with bounding preview, high confidence badge (`97.1% Confirmed`), Top-3 probability breakdown, ICAR-CICR verified remedies & research citation links. |
| **04** | `04_disease_ood_rejection.png` | **OOD / Uncertainty Rejection** | 1920 × 1080 | Uploaded non-plant or synthetic noise image triggering the Shannon Entropy rejection banner (`Out-of-Distribution / Unsupported Crop`, $H > 0.88$, $P_{\max} < 0.28$), preventing AI hallucinations. |
| **05** | `05_smart_dashboard_weather.png` | **Smart Farming Dashboard** | 1920 × 1080 | District selector (e.g. `Bhopal, Madhya Pradesh`), live Open-Meteo weather tile, 7-day temperature/humidity forecast cards, interactive SVG historical rainfall chart (30d/90d/12m), ICAR/TNAU suitability matrix. |
| **06** | `06_ai_farming_assistant.png` | **AI Farming Assistant** | 1920 × 1080 | Interactive chat UI demonstrating Gemini 2.0 Flash + Agronomic RAG retrieval, suggested prompt pills, timestamped bubble exchange, citation badges. |
| **07** | `07_mobile_responsive_view.png` | **Mobile Responsive UI** | 390 × 844 (iPhone 14) | Sliding drawer navigation, compact telemetry pill, sticky bottom navigation bar, card stacking on mobile viewport. |

---

## 2. Step-by-Step Capture Instructions

### Step 2.1: Start the Local Servers
1. Open PowerShell terminal 1 (Backend):
   ```powershell
   cd CropYieldApp\CropYieldApp\backend
   uvicorn app:app --reload --port 8001
   ```
   *Verify: `http://127.0.0.1:8001/health` returns status `healthy`.*

2. Open PowerShell terminal 2 (Frontend):
   ```powershell
   cd CropYieldApp\CropYieldApp\frontend
   npm run dev
   ```
   *Open: `http://localhost:5173` in Google Chrome or Microsoft Edge.*

---

### Step 2.2: Recommended Input Scenarios for Presentation Screenshots

#### Screenshot 01: Executive Overview (`01_overview_dashboard.png`)
- Navigate to the **Overview** tab in the sidebar.
- Ensure the header telemetry displays `System Healthy (FastAPI 8001)`.
- Capture full desktop view showing the hero banner, active models card, and system status indicators.

#### Screenshot 02: Crop Yield Prediction (`02_yield_predictor.png`)
- Navigate to **Crop Yield Prediction**.
- Fill in the benchmark scenario:
  - **Crop**: `Wheat`
  - **Region**: `North`
  - **Soil Type**: `Loam`
  - **Rainfall**: `520.0 mm`
  - **Temperature**: `21.5 °C`
  - **Fertilizer Used**: `Yes`
  - **Irrigation Used**: `Yes`
  - **Weather**: `Sunny`
  - **Days to Harvest**: `125`
- Click **"Predict Expected Crop Yield"**.
- Capture the output displaying **Random Forest** (~5,676 kg/ha), **TensorFlow DNN** (~5,836 kg/ha), **Consensus** (5,756 kg/ha / 5.76 t/ha), and the **Multi-Unit Converter** (2,329.5 kg/Acre, 1,455.9 kg/Bigha).

#### Screenshot 03: Cotton Disease Diagnosis (`03_disease_detector_cotton.png`)
- Navigate to **Plant Disease Detection**.
- Upload a holdout image from:
  `backend/data/holdout_test_images/cotton_bacterial_blight_holdout_1.jpg`
- Click **"Diagnose Leaf Disease"**.
- Capture the result showing:
  - Diagnosis: `Cotton - Bacterial Blight (Angular Leaf Spot)`
  - Confidence: `~97% (Confirmed)`
  - ICAR-CICR Nagpur & TNAU agronomic remedy protocols and citations.

#### Screenshot 04: OOD Safety Rejection (`04_disease_ood_rejection.png`)
- Upload any non-plant image (e.g., random background, car, synthetic noise pattern, or an unsupported leaf like tea or orange).
- Click **"Diagnose Leaf Disease"**.
- Capture the Amber/Red Safety Card:
  - Warning: `Uncertain or Unsupported Crop / Out-of-Distribution`
  - Shannon Entropy indicator showing high epistemic uncertainty ($H > 0.88$).
  - Explanatory message safeguarding the farmer from misdiagnosis.

#### Screenshot 05: Smart Farming Dashboard (`05_smart_dashboard_weather.png`)
- Navigate to **Smart Dashboard**.
- Select State: `Madhya Pradesh`, District: `Bhopal` (or `Indore`).
- Capture:
  - Real-time weather card (Temperature, Humidity, Wind speed, Precipitation).
  - 7-day daily forecast strip with weather icons.
  - Interactive SVG historical rainfall chart comparing 30-day, 90-day, and 12-month trends.
  - Top crop suitability cards (Maize, Wheat, Soybean) with suitability scores.

#### Screenshot 06: GenAI Farming Assistant (`06_ai_farming_assistant.png`)
- Navigate to **Farming AI Assistant**.
- Send query:
  `"What is the recommended fertilizer schedule for wheat in rabi season?"`
  *(Note: Requires `GEMINI_API_KEY` configured in `backend/.env`).*
- Capture the conversational response showing rich markdown formatting, agronomic schedule, and source citations.

#### Screenshot 07: Mobile Responsive View (`07_mobile_responsive_view.png`)
- In Google Chrome, press `F12` (or `Ctrl+Shift+I`) to open Developer Tools.
- Press `Ctrl+Shift+M` to toggle the Device Toolbar.
- Select **iPhone 14** or set dimensions to `390 × 844`.
- Capture the sliding navigation menu, compact cards, and sticky bottom navigation.

---

## 3. Chrome / Edge Clean Full-Page Capture Shortcut

To capture clean, borderless, high-resolution screenshots without browser toolbars:
1. Open DevTools (`F12`).
2. Press `Ctrl + Shift + P` (Command Menu).
3. Type: `Capture full size screenshot` and press **Enter**.
4. Save the downloaded PNG into `documentation/screenshots/` with the exact corresponding filename.
