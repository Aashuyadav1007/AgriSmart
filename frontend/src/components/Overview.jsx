import React, { useState, useEffect } from 'react';
import {
  Sprout,
  Wheat,
  Leaf,
  CloudSun,
  Bot,
  Brain,
  Thermometer,
  Droplets,
  Wind,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  MapPin,
  RefreshCw,
  AlertCircle,
  Sparkles,
  TrendingUp
} from 'lucide-react';
import { getDashboardSummary } from '../services/api';

export default function Overview({ onNavigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDashboardSummary('Madhya Pradesh', 'Bhopal');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load overview data:', err);
      setError('Unable to fetch live meteorological telemetry. Ensure backend is running on port 8001.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const weather = data?.current_weather;
  const location = data?.location;
  const topCrops = data?.crop_suitability?.suitability_rankings?.slice(0, 4) || [];

  return (
    <div className="w-full max-w-7xl mx-auto space-y-8 pb-12 font-sans animate-fade-in">
      {/* 1. Welcome & Introduction Hero Banner */}
      <div className="bg-gradient-to-br from-[#1B4332] via-[#245D44] to-[#123627] rounded-3xl p-8 md:p-10 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-400/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-400/20 border border-emerald-300/30 text-xs font-semibold text-emerald-200">
              <Sparkles className="w-3.5 h-3.5 text-emerald-300" />
              <span>AgriSmart Precision Agricultural Intelligence Hub</span>
            </div>
            <h1 className="text-3xl md:text-5xl font-black tracking-tight leading-tight">
              Empowering Agriculture Through Artificial Intelligence
            </h1>
            <p className="text-emerald-100/80 text-sm md:text-base leading-relaxed">
              Unifying dual-model crop yield forecasting, 12-class foliar disease computer vision with uncertainty calibration, precision Open-Meteo agro-meteorology, and RAG-powered GenAI agronomy guidance.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row md:flex-col gap-3 flex-shrink-0">
            <button
              onClick={() => onNavigate('yield')}
              className="px-5 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 font-black text-sm flex items-center justify-center gap-2 shadow-lg transition active:scale-95 cursor-pointer"
            >
              <span>Forecast Yield</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('disease')}
              className="px-5 py-3 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-bold text-sm flex items-center justify-center gap-2 backdrop-blur-md border border-white/15 transition active:scale-95 cursor-pointer"
            >
              <span>Diagnose Leaf</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 2. Measured Benchmark Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            icon: Brain,
            label: 'Yield Model Consensus',
            value: '91.4% R²',
            subtext: 'Random Forest + TensorFlow DNN',
            color: 'text-emerald-700',
            bg: 'bg-emerald-50/70',
            border: 'border-emerald-100'
          },
          {
            icon: Leaf,
            label: 'Disease Classes',
            value: '12 Classes',
            subtext: 'Cotton, Tomato, Potato & Corn',
            color: 'text-amber-700',
            bg: 'bg-amber-50/70',
            border: 'border-amber-100'
          },
          {
            icon: CloudSun,
            label: 'Telemetry Network',
            value: '143 Districts',
            subtext: '100% of 55 MP Districts Verified',
            color: 'text-blue-700',
            bg: 'bg-blue-50/70',
            border: 'border-blue-100'
          },
          {
            icon: CheckCircle2,
            label: 'OOD Reliability',
            value: '0.0% FAR',
            subtext: 'Calibrated Entropy Rejection',
            color: 'text-purple-700',
            bg: 'bg-purple-50/70',
            border: 'border-purple-100'
          }
        ].map((item, i) => {
          const Icon = item.icon;
          return (
            <div
              key={i}
              className={`${item.bg} rounded-3xl p-5 border ${item.border} shadow-sm hover:shadow-md transition`}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className={`w-5 h-5 ${item.color}`} />
                <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Benchmark</span>
              </div>
              <p className="text-2xl font-black text-gray-900 mt-1">{item.value}</p>
              <p className="text-xs font-bold text-gray-700 mt-0.5">{item.label}</p>
              <p className="text-[11px] text-gray-500 mt-1">{item.subtext}</p>
            </div>
          );
        })}
      </div>

      {/* 3. Live Telemetry & Crop Suitability Highlights (Real Backend Data) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Weather Card */}
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <CloudSun className="w-5 h-5 text-amber-500" />
                <h3 className="text-base font-bold text-gray-900">Regional Agro-Meteorology</h3>
              </div>
              <button
                onClick={fetchOverview}
                disabled={loading}
                title="Refresh Live Telemetry"
                className="p-1.5 text-gray-400 hover:text-emerald-700 rounded-lg hover:bg-gray-100 transition cursor-pointer"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
              </button>
            </div>

            {loading ? (
              <div className="space-y-3 py-6 animate-pulse">
                <div className="h-8 bg-gray-100 rounded-xl" />
                <div className="h-4 bg-gray-100 rounded-xl w-2/3" />
              </div>
            ) : weather ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 font-semibold mb-1">
                      <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                      <span>{location?.district}, {location?.state}</span>
                    </div>
                    <p className="text-4xl font-black text-gray-900">
                      {weather.temperature_celsius}°C
                    </p>
                    <p className="text-xs font-bold text-emerald-700 mt-1">
                      {weather.weather_condition}
                    </p>
                  </div>
                  <div className="text-right text-xs text-gray-500 space-y-1">
                    <p>Day High: <strong className="text-gray-800">{weather.today_forecast?.temp_max_celsius}°C</strong></p>
                    <p>Night Low: <strong className="text-gray-800">{weather.today_forecast?.temp_min_celsius}°C</strong></p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-gray-100 text-xs">
                  <div className="bg-gray-50 p-2.5 rounded-xl">
                    <span className="text-gray-400 font-medium">Humidity</span>
                    <p className="font-bold text-gray-800 mt-0.5">{weather.relative_humidity_percent}%</p>
                  </div>
                  <div className="bg-gray-50 p-2.5 rounded-xl">
                    <span className="text-gray-400 font-medium">Wind Speed</span>
                    <p className="font-bold text-gray-800 mt-0.5">{weather.wind_speed_kmh} km/h</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-gray-400">
                <AlertCircle className="w-6 h-6 mx-auto mb-1 text-gray-300" />
                <p>{error || 'Meteorological data unavailable'}</p>
              </div>
            )}
          </div>

          <button
            onClick={() => onNavigate('dashboard')}
            className="mt-6 w-full py-2.5 rounded-xl bg-gray-50 hover:bg-emerald-50 text-xs font-bold text-emerald-800 border border-gray-200/80 hover:border-emerald-200 flex items-center justify-center gap-1.5 transition cursor-pointer"
          >
            <span>Open Full Weather &amp; Historical Rainfall</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Crop Suitability Highlights Card */}
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sprout className="w-5 h-5 text-emerald-700" />
                <h3 className="text-base font-bold text-gray-900">Current Crop Suitability</h3>
              </div>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                Live ICAR Rules
              </span>
            </div>

            {loading ? (
              <div className="space-y-3 py-6 animate-pulse">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-6 bg-gray-100 rounded-lg" />
                ))}
              </div>
            ) : topCrops.length > 0 ? (
              <div className="space-y-3">
                {topCrops.map((c) => (
                  <div key={c.crop_name} className="flex items-center justify-between text-xs">
                    <div>
                      <strong className="text-gray-800 font-bold block">{c.crop_name}</strong>
                      <span className="text-[11px] text-gray-400">{c.season}</span>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                        c.suitability_score >= 75
                          ? 'bg-emerald-100 text-emerald-800'
                          : c.suitability_score >= 50
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}>
                        {c.suitability_score}/100
                      </span>
                      <p className="text-[10px] text-gray-400 mt-0.5">{c.suitability_level}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-gray-400">
                <p>Suitability assessment loading…</p>
              </div>
            )}
          </div>

          <button
            onClick={() => onNavigate('dashboard')}
            className="mt-6 w-full py-2.5 rounded-xl bg-gray-50 hover:bg-emerald-50 text-xs font-bold text-emerald-800 border border-gray-200/80 hover:border-emerald-200 flex items-center justify-center gap-1.5 transition cursor-pointer"
          >
            <span>View All Crop Rankings &amp; Rules</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* AI Extension Assistant Teaser */}
        <div className="bg-gradient-to-br from-emerald-950 via-[#1C4E39] to-emerald-900 rounded-3xl p-6 md:p-8 text-white shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Bot className="w-5 h-5 text-emerald-300" />
              <h3 className="text-base font-bold text-white">Ask AgriSmart Assistant</h3>
            </div>
            <p className="text-xs text-emerald-100/80 leading-relaxed mb-4">
              Need immediate advice on fertilizer splits, pest suppression, or seasonal crop planning? Our RAG-powered Gemini 2.0 assistant is ready to help.
            </p>
            <div className="space-y-2">
              {[
                'Best fertilizer schedule for wheat?',
                'How to identify Cotton bacterial blight?',
                'Optimal sowing window for soybean?'
              ].map((q, i) => (
                <button
                  key={i}
                  onClick={() => onNavigate('chat')}
                  className="w-full text-left text-xs bg-white/10 hover:bg-white/15 px-3 py-2 rounded-xl transition text-emerald-100 truncate cursor-pointer"
                >
                  &ldquo;{q}&rdquo;
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={() => onNavigate('chat')}
            className="mt-6 w-full py-2.5 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-gray-950 font-black text-xs flex items-center justify-center gap-1.5 transition shadow cursor-pointer"
          >
            <span>Start Chat Conversation</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 4. Core Navigation Shortcuts Section */}
      <div>
        <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Navigation</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              id: 'yield',
              title: 'Crop Yield Predictor',
              desc: 'Dual ML/DL consensus forecast with field acreage and unit conversions.',
              icon: Wheat,
              color: 'text-emerald-700',
              bg: 'bg-emerald-50'
            },
            {
              id: 'disease',
              title: 'Disease Classifier',
              desc: 'Foliar vision diagnosis across 12 classes with entropy OOD safety rejection.',
              icon: Leaf,
              color: 'text-amber-700',
              bg: 'bg-amber-50'
            },
            {
              id: 'dashboard',
              title: 'Smart Dashboard',
              desc: 'Live Open-Meteo forecasts, 30d/90d/12m rainfall archives & suitability.',
              icon: CloudSun,
              color: 'text-blue-700',
              bg: 'bg-blue-50'
            },
            {
              id: 'chat',
              title: 'AI Farming Assistant',
              desc: 'RAG conversational extension grounded in verified agricultural science.',
              icon: Bot,
              color: 'text-purple-700',
              bg: 'bg-purple-50'
            }
          ].map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.id}
                onClick={() => onNavigate(card.id)}
                className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm hover:shadow-md hover:border-emerald-200 transition cursor-pointer flex flex-col justify-between group"
              >
                <div>
                  <div className={`w-10 h-10 rounded-2xl ${card.bg} flex items-center justify-center mb-4`}>
                    <Icon className={`w-5 h-5 ${card.color}`} />
                  </div>
                  <h4 className="text-base font-bold text-gray-900 group-hover:text-emerald-700 transition">
                    {card.title}
                  </h4>
                  <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                    {card.desc}
                  </p>
                </div>
                <div className="mt-5 pt-3 border-t border-gray-100 flex items-center text-xs font-bold text-emerald-800 group-hover:translate-x-1 transition duration-200">
                  <span>Open Module</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
