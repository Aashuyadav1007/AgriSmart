import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Sprout, 
  Wheat, 
  Leaf, 
  CloudSun, 
  Bot, 
  BarChart3, 
  Info, 
  Menu, 
  X, 
  Thermometer, 
  Wind,
  ShieldCheck,
  ChevronRight,
  Activity,
  Home
} from 'lucide-react';
import 'react-datepicker/dist/react-datepicker.css';

import Overview from './components/Overview';
import YieldPredictor from './components/YieldPredictor';
import DiseaseDetector from './components/DiseaseDetector';
import SmartDashboard from './components/SmartDashboard';
import AgriChatbot from './components/AgriChatbot';
import AboutProject from './components/AboutProject';
import { getHealth } from './services/api';

const NAV_ITEMS = [
  { id: 'overview',   label: 'Overview',                icon: Home,       badge: null },
  { id: 'yield',      label: 'Crop Yield Prediction',   icon: Wheat,      badge: 'Dual ML' },
  { id: 'disease',    label: 'Plant Disease Detection', icon: Leaf,       badge: '12 Classes' },
  { id: 'dashboard',  label: 'Smart Dashboard',         icon: CloudSun,   badge: 'Open-Meteo' },
  { id: 'chat',       label: 'AI Farming Assistant',    icon: Bot,        badge: 'Gemini' },
  { id: 'about',      label: 'About Project',           icon: Info,       badge: null },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [weatherData, setWeatherData] = useState(null);
  const [healthData, setHealthData] = useState(null);

  // Fetch quick live weather for top bar telemetry
  useEffect(() => {
    const fetchQuickWeather = async (lat, lon) => {
      try {
        const res = await axios.get(
          `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`
        );
        setWeatherData(res.data.current_weather);
      } catch (err) {
        console.error('Top bar weather fetch error:', err);
      }
    };

    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => fetchQuickWeather(pos.coords.latitude, pos.coords.longitude),
        () => fetchQuickWeather(23.2599, 77.4126), // Default Bhopal coordinates
        { timeout: 5000 }
      );
    } else {
      fetchQuickWeather(23.2599, 77.4126);
    }

    // System health check
    getHealth().then((res) => setHealthData(res.data)).catch(() => {});
  }, []);

  const renderActiveView = () => {
    switch (activeTab) {
      case 'overview':
        return <Overview onNavigate={(tabId) => setActiveTab(tabId)} />;
      case 'yield':
        return <YieldPredictor />;
      case 'disease':
        return <DiseaseDetector />;
      case 'dashboard':
        return <SmartDashboard />;
      case 'chat':
        return <AgriChatbot />;
      case 'about':
        return <AboutProject />;
      default:
        return <Overview onNavigate={(tabId) => setActiveTab(tabId)} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAF9] flex font-sans text-gray-900 antialiased">
      {/* ===================================================================== */}
      {/* 1. DESKTOP SIDEBAR (MODERN SAAS NAVIGATION)                           */}
      {/* ===================================================================== */}
      <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-gray-200/80 sticky top-0 h-screen z-40 shadow-sm">
        {/* Brand Header */}
        <div className="p-6 border-b border-gray-100 flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#1B4332] to-[#2D6A4F] flex items-center justify-center text-white shadow-md">
            <Sprout className="w-6 h-6 text-emerald-300" />
          </div>
          <div>
            <span className="text-xl font-black text-gray-900 tracking-tight block leading-tight">
              Agri<span className="text-[#2D6A4F]">Smart</span>
            </span>
            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-700 block">
              Precision Agro-AI
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-2xl text-xs font-bold transition-all duration-150 cursor-pointer ${
                  isActive
                    ? 'bg-[#1B4332] text-white shadow-sm'
                    : 'text-gray-600 hover:bg-gray-100/70 hover:text-gray-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-300' : 'text-gray-500'}`} />
                  <span className="truncate">{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider ${
                      isActive
                        ? 'bg-emerald-400 text-emerald-950'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* System Health Status Footer Pill */}
        <div className="p-4 border-t border-gray-100 bg-gray-50/50">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-bold text-gray-700 text-[11px]">System Status</span>
            </div>
            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100/60 px-2 py-0.5 rounded-md">
              {healthData?.status === 'healthy' ? 'Active 3/3' : 'Operational'}
            </span>
          </div>
          <p className="text-[10px] text-gray-400 mt-1">Port 8001 • Fast REST APIs</p>
        </div>
      </aside>

      {/* ===================================================================== */}
      {/* 2. MAIN APPLICATION CONTENT AREA                                      */}
      {/* ===================================================================== */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-gray-200/80 px-4 md:px-8 py-3.5 flex items-center justify-between gap-4 shadow-sm">
          {/* Mobile Menu Trigger & Logo */}
          <div className="flex items-center gap-3 lg:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-gray-600 hover:bg-gray-100 transition cursor-pointer"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
            <div className="flex items-center gap-2" onClick={() => setActiveTab('overview')}>
              <Sprout className="w-6 h-6 text-[#1B4332]" />
              <span className="text-lg font-black text-gray-900 tracking-tight">
                Agri<span className="text-[#2D6A4F]">Smart</span>
              </span>
            </div>
          </div>

          {/* Current Active Section Breadcrumb (Desktop) */}
          <div className="hidden lg:flex items-center gap-2 text-xs font-semibold text-gray-400">
            <span>AgriSmart</span>
            <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
            <span className="text-gray-900 font-bold capitalize">
              {NAV_ITEMS.find((n) => n.id === activeTab)?.label || 'Intelligence Hub'}
            </span>
          </div>

          {/* Telemetry Right Badges */}
          <div className="flex items-center gap-3 ml-auto">
            {weatherData && (
              <div className="hidden sm:flex items-center gap-4 bg-emerald-50/80 border border-emerald-200/60 rounded-xl px-3.5 py-1.5 text-xs text-emerald-950 font-bold">
                <div className="flex items-center gap-1.5">
                  <CloudSun className="w-4 h-4 text-amber-500" />
                  <span>Telemetry</span>
                </div>
                <div className="flex items-center gap-1 border-l border-emerald-200 pl-3">
                  <Thermometer className="w-3.5 h-3.5 text-red-500" />
                  <span>{weatherData.temperature}°C</span>
                </div>
                <div className="flex items-center gap-1 border-l border-emerald-200 pl-3">
                  <Wind className="w-3.5 h-3.5 text-blue-500" />
                  <span>{weatherData.windspeed} km/h</span>
                </div>
              </div>
            )}

            <button
              onClick={() => setActiveTab('about')}
              className="p-2 rounded-xl border border-gray-200 text-gray-500 hover:text-emerald-800 hover:bg-emerald-50 hover:border-emerald-200 transition text-xs font-bold flex items-center gap-1.5 cursor-pointer"
            >
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span className="hidden md:inline">Verified AI</span>
            </button>
          </div>
        </header>

        {/* Mobile Slide-down Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden bg-white border-b border-gray-200 p-4 space-y-1 shadow-lg animate-fade-in z-30">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-xs font-bold transition ${
                    isActive
                      ? 'bg-[#1B4332] text-white shadow'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-gray-200/60 text-gray-700">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* Dynamic Main Body Content */}
        <main className="flex-1 p-4 md:p-8 overflow-y-auto pb-24 lg:pb-8">
          {renderActiveView()}
        </main>

        {/* Desktop Footer */}
        <footer className="hidden lg:flex items-center justify-between px-8 py-4 bg-white border-t border-gray-200/80 text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <Sprout className="w-4 h-4 text-emerald-700" />
            <span className="font-semibold text-gray-800">AgriSmart Platform v2.0</span>
            <span>• Classical ML, Deep Neural Networks, Computer Vision &amp; Gemini RAG</span>
          </div>
          <div className="flex items-center gap-4 text-gray-400">
            <span>Weather by Open-Meteo.com</span>
            <span>•</span>
            <span>Survey of India Coordinates</span>
            <span>•</span>
            <span>ICAR-CICR &amp; TNAU Validated</span>
          </div>
        </footer>

        {/* Mobile Bottom Navigation Bar */}
        <div className="lg:hidden fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 flex items-center justify-around z-40 py-2 shadow-[0_-2px_10px_rgba(0,0,0,0.06)]">
          {NAV_ITEMS.slice(0, 5).map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            const shortTitles = {
              overview: 'Home',
              yield: 'Yield',
              disease: 'Disease',
              dashboard: 'Weather',
              chat: 'AI Chat'
            };
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex flex-col items-center py-1 px-2 text-[10px] font-bold transition cursor-pointer ${
                  isActive ? 'text-[#1B4332]' : 'text-gray-400'
                }`}
              >
                <Icon className={`w-5 h-5 mb-0.5 ${isActive ? 'text-[#1B4332]' : 'text-gray-400'}`} />
                <span>{shortTitles[item.id] || item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
