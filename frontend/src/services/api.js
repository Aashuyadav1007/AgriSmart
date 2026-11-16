/**
 * AgriMind AI – Centralised API client
 * All backend calls are routed through this module.
 * The API key is NEVER stored here — it lives in backend/.env only.
 */
import axios from 'axios';

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60s for model inference
  headers: { 'Content-Type': 'application/json' },
});

// ---- Module 1: Crop Yield Prediction ----
export const predictYield = (payload) =>
  api.post('/api/yield/predict', payload);

export const getYieldMetrics = () =>
  api.get('/api/yield/metrics');

// ---- Module 2: Plant Disease Detection ----
export const detectDisease = (formData) =>
  api.post('/api/disease/detect', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const getDiseaseClasses = () =>
  api.get('/api/disease/classes');

export const getDiseaseManifest = () =>
  api.get('/api/disease/manifest');

export const getDiseaseCoverage = () =>
  api.get('/api/disease/coverage');

// ---- Module 3: GenAI Farming Assistant ----
export const chatWithAI = (message, history = []) =>
  api.post('/api/chat', { message, history });

// ---- Health ----
export const getHealth = () => api.get('/health');

// ---- Module 4: Smart Farming Dashboard & Open-Meteo Weather ----
export const getCurrentWeather = (state = 'Madhya Pradesh', district = 'Bhopal') =>
  api.get('/api/weather/current', { params: { state, district } });

export const getWeatherForecast = (state = 'Madhya Pradesh', district = 'Bhopal', days = 7) =>
  api.get('/api/weather/forecast', { params: { state, district, days } });

export const getHistoricalRainfall = (state = 'Madhya Pradesh', district = 'Bhopal', period = '30d') =>
  api.get('/api/weather/history', { params: { state, district, period } });

export const getCropSuitability = (state = 'Madhya Pradesh', district = 'Bhopal') =>
  api.get('/api/dashboard/crop-suitability', { params: { state, district } });

export const getDashboardSummary = (state = 'Madhya Pradesh', district = 'Bhopal') =>
  api.get('/api/dashboard/summary', { params: { state, district } });

export const getSupportedLocations = (state) =>
  api.get('/api/locations/districts', { params: state ? { state } : {} });

export default api;
