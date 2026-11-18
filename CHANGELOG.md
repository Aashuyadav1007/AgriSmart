# 📜 AgriSmart – Project Changelog & Release Notes

All notable changes, architectural upgrades, and feature implementations for **AgriSmart** (formerly AgriMind AI) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v2.0.0] – 2026-11-18

### 🌟 Major Highlights
* **Comprehensive Project Rebranding**: Unified project identity from *AgriMind AI* to **AgriSmart** across all frontend views, navigation bars, SVG vector logos, backend endpoints, telemetry headers, and academic defense documentation.
* **Universal Foliar Computer Vision Engine**: Enhanced PyTorch MobileNetV2 classifier with Shannon Entropy Out-of-Distribution (OOD) gating, hierarchical image quality validation, and plant organ discrimination (foliar vs. root/tuber).
* **Trilingual GenAI Extension Assistant**: Real-time Server-Sent Events (SSE) line-by-line streaming powered by **Google Gemini 2.0 Flash** grounded on a 31-topic ICAR agricultural vector knowledge base (RAG) supporting English, हिन्दी (Devanagari), and Hinglish (Roman script).
* **Precision Agro-Meteorology & MP District Geocoding**: Real-time Open-Meteo telemetry without paid API keys, supporting all 55 administrative districts of Madhya Pradesh and 143 major agricultural districts across India.

---

### 🎨 Frontend & UI/UX Upgrades (`frontend/`)
* **Brand Logo & Modern SVG Favicon**:
  - Designed custom, high-resolution vector logo (`frontend/public/favicon.svg`) featuring an emerald agricultural sprout with smart IoT intelligence nodes.
  - Updated desktop sidebar brand header and mobile header to styled typography: `Agri<span className="text-[#2D6A4F]">Smart</span>`.
  - Updated active section breadcrumbs and footer credits across all viewports.
* **Unified 6-View Responsive SaaS Navigation**:
  - Implemented desktop sticky sidebar navigation and thumb-friendly mobile bottom bar (0% horizontal scroll overflow on mobile).
  - Integrated live weather telemetry badge in top header (`Temperature °C`, `Wind km/h`).
* **Enhanced Chatbot Interface (`AgriChatbot.jsx`)**:
  - Line-by-line SSE chunk streaming with dynamic auto-scrolling.
  - Interactive Gemini API key configuration modal with dynamic hot-reload notification (no server restart required).
  - Quick-prompt chips in English, Hindi, and Hinglish.
* **Disease Vision Diagnostic UI (`DiseaseDetector.jsx`)**:
  - Camera and file-upload modes with real-time preview.
  - Multi-tier confidence visualization: High Confidence (Green), Moderate Confidence (Amber), Out-of-Distribution Rejection (Red).
  - Expandable 15-section bilingual agronomic treatment accordion (organic controls, chemical fungicides, and preventive field practices).
* **Smart Farming & Weather Dashboard (`SmartDashboard.jsx`)**:
  - 55-district Madhya Pradesh dropdown selector with instant coordinate resolution.
  - 7-day forecast cards with WMO weather codes.
  - SVG historical rainfall bar charts covering 30-day, 90-day, and 12-month periods via Copernicus ERA5 reanalysis.

---

### 🧠 Machine Learning & Computer Vision (`backend/`)
* **Module 1: Dual-Model Crop Yield Forecasting**:
  - Ensemble consensus between Random Forest Regressor ($R^2 = 0.9144, \text{MAE} = 397.16\text{ kg/ha}$) and TensorFlow Deep Neural Network ($R^2 = 0.9114, \text{MAE} = 404.17\text{ kg/ha}$).
  - Live agreement percentage calculation ($>99\%$ consensus agreement).
  - Real-time land unit conversion between metric (`kg/ha`, `ton/ha`) and Indian traditional agrarian units (`quintal/acre`, `bigha`).
* **Module 2: Plant Disease Classification & OOD Calibration**:
  - Transfer-learned PyTorch MobileNetV2 architecture with Dropout ($p=0.2$) and adapted classifier head.
  - Supported classes: Cotton (Bacterial Blight, Curl Virus, Fusarium Wilt, Healthy), Tomato (Early Blight, Late Blight, Yellow Leaf Curl, Healthy), Potato (Early Blight, Late Blight, Healthy), and Corn (Common Rust, Healthy).
  - **Hierarchical Image Quality Filter (`image_pipeline.py`)**:
    - Laplacian variance blur detection.
    - Excess Green Index (ExG) vegetation mask to reject non-plant photographs.
    - Organ discrimination routing to distinguish potato tubers and fruit from leaf foliage, preventing foliar model false positives.
  - **Shannon Entropy OOD Rejection**:
    - Normalized entropy threshold ($H(x) \ge 0.88$) and Softmax margin threshold ($< 0.50$) to reject random noise, non-crop objects, and uncalibrated plant species with 0.0% False Acceptance Rate.
  - **Bilingual ICAR/TNAU Advisory Database (`disease_remedies.json`)**:
    - Curated 16 verified disease records with complete 15-section English and Hindi agronomic guidance.
* **Module 3: Trilingual GenAI Assistant + RAG (`gemini_service.py`)**:
  - Dual-mode architecture: Live Google Gemini 2.0 Flash with automatic fallback to local RAG knowledge base.
  - Curated 31-topic ICAR agricultural vector knowledge base (`agri_knowledge_base.json`).
  - Strict language auto-detection and tone matching:
    - **Hinglish input** $\rightarrow$ Natural, conversational Hinglish response.
    - **Hindi input** $\rightarrow$ Respectful, fluent Devanagari Hindi.
    - **English input** $\rightarrow$ Clear, practical agronomic English.
  - SSE streaming endpoint (`/api/chat/stream`) yielding JSON data chunks in real time.
* **Module 4: Agro-Meteorology & District Geocoding (`services/`)**:
  - `location_service.py`: Exact latitude, longitude, and elevation mapping for 143 Indian agricultural districts (all 55 MP districts + major agricultural zones in Maharashtra, Punjab, Haryana, UP, Gujarat).
  - `weather_service.py`: Live current telemetry, 7-day numerical weather forecasts, and historical ERA5 rainfall archives via Open-Meteo CC BY 4.0 APIs.
  - `crop_suitability_service.py`: Agro-meteorological scoring evaluating temperature, humidity, and rainfall against optimal agronomic boundaries for 8 key Indian crops.

---

### 🛡️ Security, Reliability & Quality Assurance
* **Zero Credential Exposure**:
  - Environment keys strictly segregated in `backend/.env` (excluded from Git).
  - Frontend communicates purely through backend reverse-proxy endpoints without leaking client-side secrets.
* **Automated Test Suites (100% Pass Rate)**:
  - `test_universal_disease_pipeline.py`: Manifest validation, 15-section advisory integrity, non-plant rejection, organ discrimination, and Cotton holdout verification.
  - `test_district_coordinates.py`: 8/8 unit tests verifying all 55 MP districts, newly created administrative districts (Niwari, Mauganj, Maihar, Pandhurna), bounding boxes, aliases, and in-memory TTL caching.
  - `test_chat_trilingual.py`: Language classification (English, Hindi, Hinglish), conversational generation, and SSE streaming payload verification.
  - `test_stage6_e2e.py` & `validate_real_world.py`: Full regression and system health verification.

---

### 📚 Documentation & Academic Deliverables (`documentation/`)
* **[COLLEGE_DEMO_SCRIPT.md](file:///documentation/COLLEGE_DEMO_SCRIPT.md)**: 5–7 minute examiner defense script covering live click workflows, speaking points, and offline fallback contingency.
* **[VIVA_PREPARATION_GUIDE.md](file:///documentation/VIVA_PREPARATION_GUIDE.md)**: 60 technical viva questions and answers covering classical ML, MobileNetV2, Shannon Entropy, OOD calibration, Open-Meteo, and Gemini RAG.
* **[DEPLOYMENT_GUIDE.md](file:///documentation/DEPLOYMENT_GUIDE.md)**: Zero-cost cloud deployment manual (FastAPI on Render + React on Vercel).
* **[SCREENSHOTS_GUIDE.md](file:///documentation/SCREENSHOTS_GUIDE.md)**: Standard visual presentation catalog for project reports.

---

## [v1.0.0] – 2026-11-16
### Initial Release
* Initial codebase upload to GitHub repository (`https://github.com/Aashuyadav1007/AgriSmart.git`).
* Base Random Forest yield regressor and initial TensorFlow neural network model.
* Baseline MobileNetV2 disease detection model.
* React + Vite frontend skeleton and FastAPI backend integration.
