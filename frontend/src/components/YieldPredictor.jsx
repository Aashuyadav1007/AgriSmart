import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import DatePicker from 'react-datepicker';
import { differenceInDays, addDays } from 'date-fns';
import { Slider, CircularProgress } from '@mui/material';
import { Switch, message } from 'antd';
import { Leaf, MapPin, Droplet, Thermometer, Award, Tractor, ChevronDown, ChevronUp, BarChart2 } from 'lucide-react';
import axios from 'axios';

import { predictYield, getYieldMetrics } from '../services/api';
import { STATE_REGION_MAP, SOIL_TYPES, CROPS, WEATHER_CONDITIONS } from '../constants';
import indianData from '../indianDistricts.json';

export default function YieldPredictor() {
  const [formData, setFormData] = useState({
    Region: null, State: null, District: null,
    Soil_Type: null, Crop: null, Weather_Condition: null,
    Rainfall_mm: 500, Temperature_Celsius: 25,
    Fertilizer_Used: false, Irrigation_Used: false,
  });
  const [dates, setDates] = useState({
    plantingDate: new Date(),
    harvestDate: addDays(new Date(), 90),
  });
  const [loading, setLoading] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [result, setResult] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [showMetrics, setShowMetrics] = useState(false);
  const [districtOptions, setDistrictOptions] = useState([]);

  const allStates = indianData.states.map(s => ({ value: s.state, label: s.state }));

  // Load stored benchmark metrics on mount
  useEffect(() => {
    getYieldMetrics()
      .then(res => setMetrics(res.data))
      .catch(() => {});
  }, []);

  // State → region + districts
  useEffect(() => {
    if (formData.State) {
      const stateName = formData.State.value;
      const stateObj = indianData.states.find(s => s.state === stateName);
      setDistrictOptions(stateObj ? stateObj.districts.map(d => ({ value: d, label: d })) : []);
      const region = STATE_REGION_MAP[stateName] || 'North';
      setFormData(prev => ({ ...prev, Region: { value: region, label: region }, District: null }));
    } else {
      setDistrictOptions([]);
      setFormData(prev => ({ ...prev, Region: null, District: null }));
    }
  }, [formData.State]);

  // District → live weather
  useEffect(() => {
    if (!formData.District || !formData.State) return;
    const fetchDistrictWeather = async () => {
      try {
        const name = formData.District.value.split('(')[0].trim();
        const geo = await axios.get(`https://geocoding-api.open-meteo.com/v1/search?name=${name}&count=1&language=en&format=json`);
        if (geo.data.results?.length > 0) {
          const { latitude: lat, longitude: lon } = geo.data.results[0];
          const weather = await axios.get(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,precipitation&timezone=auto`);
          if (weather.data.current) {
            setFormData(prev => ({
              ...prev,
              Temperature_Celsius: weather.data.current.temperature_2m,
              Rainfall_mm: weather.data.current.precipitation,
            }));
            message.success(`Live weather synced for ${formData.District.value}`);
          }
        }
      } catch (e) {
        console.error('Weather fetch failed:', e);
      }
    };
    fetchDistrictWeather();
  }, [formData.District, formData.State]);

  const handleSelect = name => opt => setFormData(prev => ({ ...prev, [name]: opt }));
  const handleSlider = name => (_, v) => setFormData(prev => ({ ...prev, [name]: v }));
  const handleToggle = name => v => setFormData(prev => ({ ...prev, [name]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.Region || !formData.Soil_Type || !formData.Crop) {
      message.error('Please fill State, Soil Type, and Crop fields.');
      return;
    }
    const daysToHarvest = differenceInDays(dates.harvestDate, dates.plantingDate);
    if (daysToHarvest <= 0) {
      message.error('Harvest date must be after planting date.');
      return;
    }

    setLoading(true);
    setResult(null);
    const payload = {
      Region: formData.Region.value,
      Soil_Type: formData.Soil_Type.value,
      Crop: formData.Crop.value,
      Rainfall_mm: formData.Rainfall_mm,
      Temperature_Celsius: formData.Temperature_Celsius,
      Weather_Condition: formData.Weather_Condition?.value || 'Sunny',
      Fertilizer_Used: formData.Fertilizer_Used,
      Irrigation_Used: formData.Irrigation_Used,
      Days_to_Harvest: daysToHarvest,
    };

    try {
      setLoading(false);
      setIsAnimating(true);
      const [res] = await Promise.all([
        predictYield(payload),
        new Promise(r => setTimeout(r, 2500)),
      ]);
      setResult(res.data);
    } catch (err) {
      message.error(err.response?.data?.detail || 'Prediction failed. Is the backend running?');
    } finally {
      setLoading(false);
      setIsAnimating(false);
    }
  };

  const agreementColor = pct =>
    pct >= 95 ? 'bg-green-100 text-green-800 border-green-200' :
    pct >= 85 ? 'bg-yellow-100 text-yellow-800 border-yellow-200' :
                'bg-orange-100 text-orange-800 border-orange-200';

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <div className="bg-white rounded-3xl shadow-lg p-6 md:p-10 border border-gray-100">
        <div className="flex items-center gap-3 mb-8 pb-4 border-b border-gray-200">
          <Leaf className="w-6 h-6 text-[#2B6049]" />
          <h2 className="text-2xl font-bold text-gray-800">Crop Yield Prediction</h2>
          <span className="ml-auto text-xs text-gray-400 font-medium">RF + TensorFlow Dual Model</span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8 text-left">
          {/* Location */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-600">Country</label>
              <input disabled value="India" className="w-full px-4 py-2 bg-gray-100 border border-gray-200 rounded-lg cursor-not-allowed text-gray-500" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-600">State *</label>
              <Select options={allStates} value={formData.State} onChange={handleSelect('State')} isClearable placeholder="Select State" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-600">District</label>
              <Select options={districtOptions} value={formData.District} onChange={handleSelect('District')} isClearable placeholder="Select District" isDisabled={!formData.State} />
            </div>
          </div>

          {/* Crop details */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-600">Soil Type *</label>
              <Select options={SOIL_TYPES} value={formData.Soil_Type} onChange={handleSelect('Soil_Type')} isClearable placeholder="Select Soil" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-600">Crop *</label>
              <Select options={CROPS} value={formData.Crop} onChange={handleSelect('Crop')} isClearable placeholder="Select Crop" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-600">Weather Condition</label>
              <Select options={WEATHER_CONDITIONS} value={formData.Weather_Condition} onChange={handleSelect('Weather_Condition')} isClearable placeholder="Select Weather" />
            </div>
          </div>

          {/* Sliders */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 bg-gray-50 p-6 rounded-2xl border border-gray-100">
            <div>
              <label className="flex items-center gap-2 text-sm font-semibold mb-4 text-gray-600">
                <Droplet className="w-4 h-4 text-blue-500" /> Rainfall (mm):&nbsp;<span className="text-blue-600">{formData.Rainfall_mm}</span>
              </label>
              <Slider value={formData.Rainfall_mm} onChange={handleSlider('Rainfall_mm')} min={0} max={3000} sx={{ color: '#3b82f6', height: 8 }} />
            </div>
            <div>
              <label className="flex items-center gap-2 text-sm font-semibold mb-4 text-gray-600">
                <Thermometer className="w-4 h-4 text-red-500" /> Avg Temperature (°C):&nbsp;<span className="text-red-500">{formData.Temperature_Celsius}</span>
              </label>
              <Slider value={formData.Temperature_Celsius} onChange={handleSlider('Temperature_Celsius')} min={-10} max={60} sx={{ color: '#ef4444', height: 8 }} />
            </div>
          </div>

          {/* Dates & Toggles */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-end">
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-600">Planting Date</label>
              <DatePicker selected={dates.plantingDate} onChange={d => setDates(p => ({ ...p, plantingDate: d }))} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#2B6049]" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-600">Harvest Date</label>
              <DatePicker selected={dates.harvestDate} onChange={d => setDates(p => ({ ...p, harvestDate: d }))} minDate={dates.plantingDate} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#2B6049]" />
            </div>
            <div className="flex items-center justify-between px-4 py-2 border border-gray-200 rounded-lg bg-gray-50">
              <span className="font-semibold text-gray-600 text-sm">Fertilizer Used</span>
              <Switch checked={formData.Fertilizer_Used} onChange={handleToggle('Fertilizer_Used')} style={{ background: formData.Fertilizer_Used ? '#2B6049' : 'rgba(0,0,0,0.25)' }} />
            </div>
            <div className="flex items-center justify-between px-4 py-2 border border-gray-200 rounded-lg bg-gray-50">
              <span className="font-semibold text-gray-600 text-sm">Irrigation Used</span>
              <Switch checked={formData.Irrigation_Used} onChange={handleToggle('Irrigation_Used')} style={{ background: formData.Irrigation_Used ? '#3b82f6' : 'rgba(0,0,0,0.25)' }} />
            </div>
          </div>

          <div className="flex justify-start pt-4 border-t border-gray-200">
            <button type="submit" disabled={loading || isAnimating} className="px-10 py-3 bg-[#2B6049] hover:bg-[#204a37] text-white font-bold rounded-lg shadow-lg transition active:scale-95 focus:ring-4 focus:ring-[#2B6049]/50 disabled:opacity-70 flex items-center gap-3">
              {loading ? <CircularProgress size={20} color="inherit" /> : <><Award className="w-5 h-5" /> Predict Crop Yield</>}
            </button>
          </div>
        </form>

        {/* Tractor Animation */}
        {isAnimating && (
          <div className="mt-8 overflow-hidden relative h-28 bg-[#e8f3ee] border-2 border-[#2B6049]/20 rounded-2xl flex items-center shadow-inner">
            <div className="absolute animate-tractor"><Tractor className="w-14 h-14 text-[#2B6049]" /></div>
            <p className="w-full text-center text-[#2B6049] font-bold text-lg animate-pulse">Calculating optimal yield…</p>
          </div>
        )}

        {/* Results */}
        {!isAnimating && result && (
          <div className="mt-8 space-y-4 animate-fade-in">
            {/* Three prediction cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* RF */}
              <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 text-center">
                <p className="text-xs font-bold uppercase tracking-widest text-blue-500 mb-1">Random Forest</p>
                <p className="text-3xl font-black text-blue-700">{result.predictions.random_forest.yield_kg_per_ha.toLocaleString('en-IN')}</p>
                <p className="text-sm text-blue-500 font-semibold">kg / ha</p>
              </div>
              {/* TF */}
              <div className="bg-purple-50 border border-purple-200 rounded-2xl p-5 text-center">
                <p className="text-xs font-bold uppercase tracking-widest text-purple-500 mb-1">TensorFlow DNN</p>
                <p className="text-3xl font-black text-purple-700">
                  {result.predictions.tensorflow_dnn.yield_kg_per_ha?.toLocaleString('en-IN') ?? 'N/A'}
                </p>
                <p className="text-sm text-purple-500 font-semibold">kg / ha</p>
              </div>
              {/* Consensus */}
              <div className="bg-green-50 border-2 border-[#2B6049]/30 rounded-2xl p-5 text-center relative">
                <p className="text-xs font-bold uppercase tracking-widest text-[#2B6049] mb-1">Ensemble Consensus</p>
                <p className="text-3xl font-black text-[#2B6049]">{result.predictions.ensemble_consensus.yield_kg_per_ha.toLocaleString('en-IN')}</p>
                <p className="text-sm text-[#2B6049] font-semibold">kg / ha</p>
                <span className={`mt-2 inline-block text-xs font-bold px-2 py-0.5 rounded-full border ${agreementColor(result.predictions.ensemble_consensus.model_agreement_percentage)}`}>
                  {result.predictions.ensemble_consensus.model_agreement_percentage}% agreement
                </span>
              </div>
            </div>

            {/* Unit conversions */}
            <div className="grid grid-cols-3 gap-3">
              {[
                ['Per Acre', (result.predictions.ensemble_consensus.yield_kg_per_ha / 2.47105).toFixed(2)],
                ['Per Bigha', (result.predictions.ensemble_consensus.yield_kg_per_ha / 3.953686).toFixed(2)],
                ['Per Gaj', (result.predictions.ensemble_consensus.yield_kg_per_ha / 11959.9).toFixed(4)],
              ].map(([label, val]) => (
                <div key={label} className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between shadow-sm">
                  <span className="text-gray-500 font-semibold text-xs uppercase tracking-wide">{label}</span>
                  <span className="text-gray-800 font-bold">{val} kg</span>
                </div>
              ))}
            </div>

            {/* Model metrics collapsible */}
            {metrics && (() => {
              const rf = metrics.models?.random_forest || metrics.random_forest || {};
              const tf = metrics.models?.tensorflow_dnn || metrics.tensorflow_dnn || {};
              const rfR2 = (rf.r2_score ?? rf.r2)?.toFixed(4) || 'N/A';
              const rfMae = (rf.mae_kg_per_ha ?? rf.mae)?.toFixed(1) || 'N/A';
              const tfR2 = (tf.r2_score ?? tf.r2)?.toFixed(4) || 'N/A';
              const tfMae = (tf.mae_kg_per_ha ?? tf.mae)?.toFixed(1) || 'N/A';
              return (
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <button onClick={() => setShowMetrics(v => !v)} className="w-full flex items-center justify-between px-5 py-3 bg-gray-50 text-sm font-semibold text-gray-600 hover:bg-gray-100 transition">
                    <span className="flex items-center gap-2"><BarChart2 className="w-4 h-4" /> Model Performance Benchmarks</span>
                    {showMetrics ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                  {showMetrics && (
                    <div className="p-5 bg-white">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                        {[
                          ['RF R²', rfR2],
                          ['RF MAE', `${rfMae} kg/ha`],
                          ['TF R²', tfR2],
                          ['TF MAE', `${tfMae} kg/ha`],
                        ].map(([label, val]) => (
                          <div key={label} className="bg-gray-50 rounded-lg p-3">
                            <p className="text-xs text-gray-500 font-semibold uppercase">{label}</p>
                            <p className="text-lg font-bold text-gray-800">{val}</p>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-gray-400 mt-3 text-center">Evaluated on 20,000 held-out test samples. Test split seed=42.</p>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
