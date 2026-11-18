import React from 'react';
import { 
  Brain, 
  Leaf, 
  CloudSun, 
  Bot, 
  ShieldCheck, 
  Database, 
  Layers, 
  Award, 
  ExternalLink,
  Code2,
  CheckCircle2
} from 'lucide-react';

export default function AboutProject() {
  return (
    <div className="w-full max-w-6xl mx-auto space-y-8 pb-12 font-sans animate-fade-in">
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-[#1B4332] via-[#2D6A4F] to-[#123627] rounded-3xl p-8 md:p-10 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-400/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-400/20 border border-emerald-300/30 text-xs font-semibold text-emerald-200 mb-4">
            <ShieldCheck className="w-4 h-4 text-emerald-300" />
            <span>Enterprise Multi-Modal Agricultural Intelligence</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black tracking-tight mb-3">
            About AgriSmart
          </h1>
          <p className="text-emerald-100/90 text-sm md:text-base leading-relaxed">
            AgriSmart is an enterprise-grade Smart Agriculture platform unifying classical Machine Learning, Deep Neural Networks, Computer Vision with Out-of-Distribution (OOD) uncertainty calibration, Open-Meteo telemetry, and Generative AI (RAG).
          </p>
        </div>
      </div>

      {/* 4 Core Pillars Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Module 1 */}
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm hover:shadow-md transition">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-2xl bg-emerald-50 text-emerald-800">
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Dual-Model Yield Forecasting</h3>
              <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Module 1 • ML & DL</span>
            </div>
          </div>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Combines an ensemble Random Forest Regressor (<strong className="text-gray-900">R² = 0.9144, MAE = 397 kg/ha</strong>) and a TensorFlow Feedforward Deep Neural Network (<strong className="text-gray-900">R² = 0.9114, MAE = 404 kg/ha</strong>) trained on 1,000,000 national crop records. Features real-time consensus agreement (&gt;99%) and multi-unit conversions (kg/ha, tons/ha, quintals/acre, bigha).
          </p>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-semibold">Random Forest</span>
            <span className="px-2.5 py-1 rounded-lg bg-purple-50 text-purple-700 font-semibold">TensorFlow DNN</span>
            <span className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 font-semibold">Consensus Engine</span>
          </div>
        </div>

        {/* Module 2 */}
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm hover:shadow-md transition">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-2xl bg-amber-50 text-amber-800">
              <Leaf className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Plant Disease Vision & OOD Rejection</h3>
              <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Module 2 • Computer Vision</span>
            </div>
          </div>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Employs PyTorch MobileNetV2 transfer learning across 12 health classes spanning Cotton, Tomato, Potato, and Corn. Integrates Shannon entropy Out-of-Distribution calibration to safely reject non-plant images and unfamiliar foliage with 0% false acceptance. Integrated remedies database citations include ICAR-CICR and TNAU.
          </p>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-700 font-semibold">MobileNetV2</span>
            <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-semibold">12 Classes + Cotton</span>
            <span className="px-2.5 py-1 rounded-lg bg-red-50 text-red-700 font-semibold">Entropy OOD Rejection</span>
          </div>
        </div>

        {/* Module 3 */}
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm hover:shadow-md transition">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-2xl bg-blue-50 text-blue-800">
              <CloudSun className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Precision Agro-Meteorology</h3>
              <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Module 3 • Open-Meteo & Geocoding</span>
            </div>
          </div>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Live telemetry without API keys using Open-Meteo Forecast and ERA5 Historical Reanalysis APIs. Supported by a verified Survey of India coordinates database for 143 agricultural districts, including all 55 administrative districts of Madhya Pradesh. Evaluates 8 major crops against documented agronomic rules.
          </p>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 font-semibold">55 MP Districts</span>
            <span className="px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 font-semibold">ERA5 Rainfall Archives</span>
            <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-semibold">Crop Suitability</span>
          </div>
        </div>

        {/* Module 4 */}
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm hover:shadow-md transition">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-2xl bg-purple-50 text-purple-800">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">GenAI Farming Assistant (RAG)</h3>
              <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Module 4 • Gemini 2.0 Flash</span>
            </div>
          </div>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Conversational agricultural extension assistant powered by Google Gemini 2.0 Flash combined with a curated 31-topic vector knowledge base covering Indian cropping calendars, NPK nutrient balances, organic pesticides, micro-irrigation systems, and pest controls.
          </p>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-lg bg-purple-50 text-purple-700 font-semibold">Gemini 2.0 Flash</span>
            <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-semibold">RAG Knowledge Base</span>
            <span className="px-2.5 py-1 rounded-lg bg-gray-100 text-gray-700 font-semibold">Zero Client Secret Leak</span>
          </div>
        </div>
      </div>

      {/* Empirical Benchmarks Table */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <Award className="w-5 h-5 text-emerald-700" />
          <h3 className="text-lg font-bold text-gray-900">Measured Empirical Performance Benchmarks</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-gray-500 text-left">
                <th className="py-3 px-4 font-semibold">Subsystem / Model</th>
                <th className="py-3 px-4 font-semibold">Dataset / Scope</th>
                <th className="py-3 px-4 font-semibold">Key Empirical Metric</th>
                <th className="py-3 px-4 font-semibold">Verification Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              <tr>
                <td className="py-3 px-4 font-bold text-gray-900">Random Forest Regressor</td>
                <td className="py-3 px-4 text-xs text-gray-500">20,000 Held-Out Test Records (Seed 42)</td>
                <td className="py-3 px-4"><span className="font-bold text-emerald-700">R² = 0.9144</span>, MAE = 397.16 kg/ha</td>
                <td className="py-3 px-4 text-xs font-bold text-emerald-800">Verified Test Set</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-gray-900">TensorFlow Deep Neural Network</td>
                <td className="py-3 px-4 text-xs text-gray-500">20,000 Held-Out Test Records (Seed 42)</td>
                <td className="py-3 px-4"><span className="font-bold text-purple-700">R² = 0.9114</span>, MAE = 404.17 kg/ha</td>
                <td className="py-3 px-4 text-xs font-bold text-emerald-800">Verified Test Set</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-gray-900">PyTorch MobileNetV2 (12 Classes)</td>
                <td className="py-3 px-4 text-xs text-gray-500">23 Held-Out Test Images + 19 Independent Holdouts</td>
                <td className="py-3 px-4"><span className="font-bold text-amber-700">73.91% Test Acc</span>, 78.26% Best Val Acc</td>
                <td className="py-3 px-4 text-xs font-bold text-emerald-800">Verified Test Set</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-gray-900">Entropy Out-of-Distribution Detector</td>
                <td className="py-3 px-4 text-xs text-gray-500">Synthetic Noise &amp; Non-Crop Foliage</td>
                <td className="py-3 px-4"><span className="font-bold text-emerald-700">0.0% False Acceptance</span> (FAR)</td>
                <td className="py-3 px-4 text-xs font-bold text-emerald-800">Calibrated Rejection</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-gray-900">District Geocoding Service</td>
                <td className="py-3 px-4 text-xs text-gray-500">Survey of India (55 MP Districts + Major India)</td>
                <td className="py-3 px-4"><span className="font-bold text-blue-700">143 Districts</span>, 100% Boundary Validated</td>
                <td className="py-3 px-4 text-xs font-bold text-emerald-800">Automated Suite (8/8)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Academic & Research Citations */}
      <div className="bg-gray-50 rounded-3xl p-6 md:p-8 border border-gray-200">
        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-4">
          Official Data Sources &amp; Institutional Citations
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-gray-600">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span><strong>ICAR-CICR Nagpur:</strong> Integrated disease management protocols and chemical thresholds for Cotton.</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span><strong>TNAU Agritech Portal:</strong> Crop protection database and pathology recommendations.</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span><strong>Directorate of Economics and Statistics (DES):</strong> National crop yield historical baseline statistics.</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span><strong>Open-Meteo &amp; Copernicus ERA5:</strong> Non-commercial CC BY 4.0 weather telemetry and reanalysis archives.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
