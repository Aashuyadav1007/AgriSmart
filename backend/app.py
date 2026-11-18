from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import joblib
import pandas as pd
import numpy as np
import os

# Suppress noisy logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
from tensorflow import keras

from path_config import RF_MODEL_PATH, TF_MODEL_PATH, METRICS_PATH, BACKEND_DIR, DISEASE_CLASSES_PATH
from services.disease_service import disease_service
from services import gemini_service
from services.location_service import location_service
from services.weather_service import weather_service
from services.crop_suitability_service import crop_suitability_service

app = FastAPI(
    title="AgriSmart - Smart Agriculture Intelligence API",
    version="2.0.0",
    description="Full-stack AI-Powered Smart Agriculture Intelligence System backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model state
rf_pipeline = None
tf_model = None
benchmark_metrics = None

@app.on_event("startup")
def load_all_models():
    global rf_pipeline, tf_model, benchmark_metrics
    
    # 1. Load Random Forest
    if RF_MODEL_PATH.exists():
        try:
            rf_pipeline = joblib.load(RF_MODEL_PATH)
            print(f"[OK] Random Forest Model loaded from {RF_MODEL_PATH}")
        except Exception as e:
            print(f"[ERROR] Failed to load Random Forest model: {e}")
    else:
        print(f"[WARNING] RF Model not found at {RF_MODEL_PATH}")

    # 2. Load TensorFlow Model
    if TF_MODEL_PATH.exists():
        try:
            tf_model = keras.models.load_model(TF_MODEL_PATH)
            print(f"[OK] TensorFlow Model loaded from {TF_MODEL_PATH}")
        except Exception as e:
            print(f"[ERROR] Failed to load TensorFlow model: {e}")
    else:
        print(f"[WARNING] TF Model not found at {TF_MODEL_PATH}")

    # 3. Load Comparison Metrics
    if METRICS_PATH.exists():
        try:
            with open(METRICS_PATH, "r") as f:
                benchmark_metrics = json.load(f)
            print(f"[OK] Benchmark metrics loaded from {METRICS_PATH}")
        except Exception as e:
            print(f"[ERROR] Failed to load metrics: {e}")

    # 4. PyTorch Disease Service is initialized on import and reloads on startup
    disease_service.load_metadata_and_model()


# ==========================================
# MODULE 1: CROP YIELD PREDICTION & METRICS
# ==========================================

class CropYieldRequest(BaseModel):
    Region: str = Field(..., description="Geographical region: North, South, East, West")
    Soil_Type: str = Field(..., description="Soil type: Sandy, Clay, Loam, Silt, Peaty, Chalky")
    Crop: str = Field(..., description="Target crop: Cotton, Rice, Barley, Soybean, Wheat, Maize")
    Rainfall_mm: float = Field(..., ge=0, le=5000, description="Annual/seasonal rainfall in mm")
    Temperature_Celsius: float = Field(..., ge=-10, le=60, description="Temperature in Celsius")
    Weather_Condition: Optional[str] = Field("Sunny", description="Weather condition: Sunny, Cloudy, Rainy")
    Fertilizer_Used: bool = Field(..., description="True if fertilizer was applied")
    Irrigation_Used: bool = Field(..., description="True if artificial irrigation was used")
    Days_to_Harvest: int = Field(..., ge=10, le=400, description="Growth cycle length in days")

    model_config = {
        "json_schema_extra": {
            "example": {
                "Region": "North",
                "Soil_Type": "Loam",
                "Crop": "Wheat",
                "Rainfall_mm": 650.0,
                "Temperature_Celsius": 23.5,
                "Weather_Condition": "Sunny",
                "Fertilizer_Used": True,
                "Irrigation_Used": True,
                "Days_to_Harvest": 120
            }
        }
    }

@app.get("/")
def read_root():
    return {
        "status": "active",
        "system": "AgriSmart Platform",
        "version": "2.0.0",
        "modules": {
            "module_1": "Crop Yield Forecasting (RF & TensorFlow)",
            "module_2": "Plant Disease Classification (PyTorch MobileNetV2)",
            "module_3": "GenAI Farming Assistant (Gemini & RAG)",
            "module_4": "Smart Dashboard & Telemetry"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "rf_model_loaded": rf_pipeline is not None,
        "tf_model_loaded": tf_model is not None,
        "disease_model_loaded": disease_service.model is not None,
        "metrics_available": benchmark_metrics is not None
    }

@app.get("/api/yield/metrics")
def get_yield_metrics():
    """Returns stored benchmark evaluation metrics comparing Random Forest and TensorFlow."""
    if benchmark_metrics is None:
        raise HTTPException(status_code=404, detail="Benchmark metrics not yet computed.")
    return benchmark_metrics

@app.post("/predict")
def legacy_predict(req: CropYieldRequest):
    """Preserves 100% backwards compatibility with original frontend contract."""
    if rf_pipeline is None:
        raise HTTPException(status_code=500, detail="Random Forest model is not loaded.")
    
    try:
        data = {
            'Region': [req.Region],
            'Soil_Type': [req.Soil_Type],
            'Crop': [req.Crop],
            'Rainfall_mm': [req.Rainfall_mm],
            'Temperature_Celsius': [req.Temperature_Celsius],
            'Weather_Condition': [req.Weather_Condition or "Sunny"],
            'Fertilizer_Used': [int(req.Fertilizer_Used)],
            'Irrigation_Used': [int(req.Irrigation_Used)],
            'Days_to_Harvest': [req.Days_to_Harvest]
        }
        df = pd.DataFrame(data)
        prediction = rf_pipeline.predict(df)
        predicted_tons = float(prediction[0])
        return {
            "predicted_yield_kg_per_hectare": round(predicted_tons * 1000, 2),
            "predicted_yield_tons_per_hectare": round(predicted_tons, 4),
            "model_used": "Random Forest Regressor"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/yield/predict")
def predict_yield_comparison(req: CropYieldRequest):
    """
    AgriSmart Module 1 Endpoint:
    Returns dual predictions from both Random Forest and TensorFlow models
    alongside ensemble consensus and actual stored performance metrics.
    """
    if rf_pipeline is None:
        raise HTTPException(status_code=500, detail="Random Forest model is not initialized.")
    
    try:
        data = {
            'Region': [req.Region],
            'Soil_Type': [req.Soil_Type],
            'Crop': [req.Crop],
            'Rainfall_mm': [req.Rainfall_mm],
            'Temperature_Celsius': [req.Temperature_Celsius],
            'Weather_Condition': [req.Weather_Condition or "Sunny"],
            'Fertilizer_Used': [int(req.Fertilizer_Used)],
            'Irrigation_Used': [int(req.Irrigation_Used)],
            'Days_to_Harvest': [req.Days_to_Harvest]
        }
        df = pd.DataFrame(data)
        
        # 1. Random Forest prediction
        rf_pred_tons = float(rf_pipeline.predict(df)[0])
        rf_pred_kg = round(rf_pred_tons * 1000, 2)
        
        # 2. TensorFlow prediction using identical preprocessor
        tf_pred_tons = None
        tf_pred_kg = None
        if tf_model is not None:
            preprocessor = rf_pipeline.named_steps['preprocessor']
            X_trans = preprocessor.transform(df)
            if hasattr(X_trans, 'toarray'):
                X_trans = X_trans.toarray()
            tf_out = tf_model.predict(X_trans, verbose=0)
            tf_pred_tons = float(tf_out[0][0])
            tf_pred_kg = round(tf_pred_tons * 1000, 2)
            
            # Ensemble consensus
            ensemble_tons = round((rf_pred_tons + tf_pred_tons) / 2.0, 4)
            ensemble_kg = round(ensemble_tons * 1000, 2)
            diff_kg = round(abs(rf_pred_kg - tf_pred_kg), 2)
            consensus_pct = round(max(0, 100 - (diff_kg / max(rf_pred_kg, 1.0) * 100)), 1)
        else:
            ensemble_tons = rf_pred_tons
            ensemble_kg = rf_pred_kg
            diff_kg = 0.0
            consensus_pct = 100.0

        return {
            "predictions": {
                "random_forest": {
                    "yield_kg_per_ha": rf_pred_kg,
                    "yield_tons_per_ha": round(rf_pred_tons, 4)
                },
                "tensorflow_dnn": {
                    "yield_kg_per_ha": tf_pred_kg,
                    "yield_tons_per_ha": round(tf_pred_tons, 4) if tf_pred_tons is not None else None
                },
                "ensemble_consensus": {
                    "yield_kg_per_ha": ensemble_kg,
                    "yield_tons_per_ha": ensemble_tons,
                    "model_agreement_percentage": consensus_pct,
                    "difference_kg_per_ha": diff_kg
                }
            },
            "benchmark_metrics": benchmark_metrics,
            "input_parameters": req.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===============================================
# MODULE 2: PYTORCH PLANT DISEASE CLASSIFICATION
# ===============================================

@app.get("/api/disease/classes")
def get_detectable_diseases():
    """Returns all plant disease classes detectable by the PyTorch MobileNetV2 model."""
    return {
        "total_classes": len(disease_service.class_names),
        "classes": disease_service.class_names,
        "remedies_available": list(disease_service.remedies_db.keys())
    }

@app.get("/api/disease/manifest")
def get_disease_dataset_manifest():
    """Returns verified dataset manifest with image counts, licenses, and sources."""
    manifest_path = BACKEND_DIR / "data" / "crop_disease_dataset_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Dataset manifest not found")

@app.get("/api/disease/coverage")
def get_crop_disease_coverage():
    """Returns comprehensive 17-crop coverage matrix across Kharif, Rabi, and Horticulture."""
    manifest_path = BACKEND_DIR / "data" / "crop_disease_dataset_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "total_crops": data.get("total_crops_cataloged", 17),
                "summary": data.get("summary", {}),
                "crops": data.get("crop_categories", [])
            }
    raise HTTPException(status_code=404, detail="Coverage database not found")

@app.post("/api/disease/detect")
async def detect_plant_disease(file: UploadFile = File(...)):
    """
    AgriSmart Module 2 Endpoint:
    Upload a plant leaf image (JPEG, PNG, WEBP, max 10MB) to diagnose plant disease,
    confidence score (softmax), symptoms, and scientifically verified organic/chemical treatments.
    """
    # 1. Read file bytes
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")
    
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 2. Strict validation (format and size)
    is_valid, error_msg = disease_service.validate_image_bytes(contents, max_mb=10.0)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # 3. Model inference and remedy synthesis
    try:
        result = disease_service.predict_leaf_disease(contents)
        result["file_name"] = file.filename
        result["file_size_bytes"] = len(contents)
        return result
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

# =============================================
# MODULE 3: GEMINI AI FARMING ASSISTANT + RAG
# =============================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's agricultural question")
    history: List[Dict[str, str]] = Field(default=[], description="Previous chat turns [{role, content}]")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "What is the best fertilizer for wheat?",
                "history": []
            }
        }
    }

@app.post("/api/chat")
async def farming_assistant(req: ChatRequest):
    """
    AgriSmart Module 3 Endpoint:
    Chat with the Gemini-powered AI farming assistant.
    Uses RAG with verified agricultural knowledge base.
    Supports English, Hindi, and Hinglish.
    """
    try:
        result = gemini_service.chat(
            message=req.message,
            history=req.history,
            top_k_context=3
        )
        return {
            "reply": result["reply"],
            "context_topics": result["context_topics"],
            "context_used": result["context_used"],
            "model": result.get("engine", "gemini-2.0-flash"),
            "is_live_gemini": result.get("is_live_gemini", False),
            "language": result.get("language", "english"),
            "status": result.get("status", "active")
        }
    except EnvironmentError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "GEMINI_API_KEY not configured",
                "message": str(e),
                "setup": "Add GEMINI_API_KEY=<your_key> to backend/.env then restart the server."
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/api/chat/stream")
async def farming_assistant_stream(req: ChatRequest):
    """
    AgriSmart Module 3 Streaming Endpoint:
    Real-time generative token/line streaming via Server-Sent Events (SSE).
    Generates dynamic answers line-by-line in English, Hindi, or Hinglish.
    """
    try:
        return StreamingResponse(
            gemini_service.chat_stream(
                message=req.message,
                history=req.history,
                top_k_context=3
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")


# ============================================================================
# STAGE 5: WEATHER, HISTORICAL RAINFALL & SMART DASHBOARD ENDPOINTS
# ============================================================================

@app.get("/api/locations/districts")
def get_supported_locations(state: Optional[str] = None):
    """Returns list of supported states and verified districts."""
    if state:
        districts = location_service.get_districts_for_state(state)
        return {
            "state": state,
            "districts_count": len(districts),
            "districts": districts
        }
    return {
        "total_states": len(location_service.get_supported_states()),
        "states": location_service.get_supported_states()
    }


@app.get("/api/weather/current")
def get_current_weather_endpoint(
    state: str = Query("Madhya Pradesh", description="Indian state name"),
    district: str = Query("Bhopal", description="District name")
):
    """
    Fetches real-time weather observations for a district via Open-Meteo API.
    Uses verified geographic coordinates from district_coordinates.json.
    """
    try:
        return weather_service.get_current_weather(state, district)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather service unavailable: {str(e)}")


@app.get("/api/weather/forecast")
def get_weather_forecast_endpoint(
    state: str = Query("Madhya Pradesh", description="Indian state name"),
    district: str = Query("Bhopal", description="District name"),
    days: int = Query(7, ge=1, le=14, description="Forecast days (1-14)")
):
    """
    Fetches upcoming numerical weather prediction forecast for a district.
    """
    try:
        return weather_service.get_forecast(state, district, days=days)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Forecast service unavailable: {str(e)}")


@app.get("/api/weather/history")
def get_weather_history_endpoint(
    state: str = Query("Madhya Pradesh", description="Indian state name"),
    district: str = Query("Bhopal", description="District name"),
    period: str = Query("30d", pattern="^(30d|90d|12m)$", description="Selectable period: 30d, 90d, or 12m")
):
    """
    Fetches historical precipitation and temperature observations from Open-Meteo Archive API.
    Clearly distinguishes reanalysis observations from forecast models.
    """
    try:
        return weather_service.get_historical_rainfall(state, district, period=period)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Historical weather archive unavailable: {str(e)}")


@app.get("/api/dashboard/crop-suitability")
def get_crop_suitability_endpoint(
    state: str = Query("Madhya Pradesh", description="Indian state name"),
    district: str = Query("Bhopal", description="District name")
):
    """
    Calculates agro-meteorological suitability scores for major Indian crops
    using live weather, 30-day cumulative rainfall, and documented agronomic thresholds.
    """
    try:
        return crop_suitability_service.evaluate_suitability(state, district)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crop suitability calculation failed: {str(e)}")


@app.get("/api/dashboard/summary")
def get_dashboard_summary_endpoint(
    state: str = Query("Madhya Pradesh", description="Indian state name"),
    district: str = Query("Bhopal", description="District name")
):
    """
    Aggregated endpoint returning live weather, 7-day forecast, 30-day historical rainfall,
    and crop suitability rankings for the Smart Farming Dashboard in a single round-trip.
    """
    try:
        current_wx = weather_service.get_current_weather(state, district)
        forecast_wx = weather_service.get_forecast(state, district, days=7)
        history_30d = weather_service.get_historical_rainfall(state, district, period="30d")
        suitability = crop_suitability_service.evaluate_suitability(state, district)

        return {
            "status": "success",
            "location": current_wx["location"],
            "current_weather": current_wx,
            "forecast_7d": forecast_wx,
            "historical_rainfall_30d": history_30d,
            "crop_suitability": suitability,
            "system_status": {
                "rf_model_active": rf_pipeline is not None,
                "tf_model_active": tf_model is not None,
                "disease_classifier_active": disease_service.model is not None
            },
            "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)"
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Dashboard summary aggregation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
