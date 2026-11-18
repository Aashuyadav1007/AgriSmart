import React, { useState, useRef, useEffect } from 'react';
import { CircularProgress } from '@mui/material';
import { 
  Send, Bot, User, Sparkles, AlertCircle, Key, ExternalLink, 
  HelpCircle, CheckCircle, Info, ShieldCheck, ChevronRight, X, Radio
} from 'lucide-react';
import { chatWithAI, BASE_URL } from '../services/api';

const STARTER_QUESTIONS = [
  { label: '🌾 Wheat Fertilizer (English)', query: 'What is the recommended fertilizer schedule for wheat in rabi season?' },
  { label: '🚜 गेहूँ में पहला पानी (Hinglish)', query: 'bhai gehu ki fasal me pehla pani kab dena chahiye aur konsi khad dale' },
  { label: '🌿 गेहूँ में खाद की सही मात्रा (हिन्दी)', query: 'गेहूँ की फसल में कौन सा खाद और कितनी मात्रा में डालना चाहिए?' },
  { label: '🐛 Kapas me rog roktham (Hinglish)', query: 'kapas me patti mudne ka rog kaise thik kare koi asardaar dawa batao' },
  { label: '🥔 आलू का पछेती झुलसा (हिन्दी)', query: 'आलू में पछेती झुलसा (Late Blight) रोग से बचाव के क्या उपाय हैं?' },
  { label: '🌧️ Malwa MP Soil Suitability (English)', query: 'What crops grow best in black clay soil of Malwa region, Madhya Pradesh?' },
];

export default function AgriChatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'model',
      content: "👋 **नमस्ते किसान भाई! / Hello!** I am **AgriSmart**, your trilingual intelligent farming assistant.\n\nAsk me anything in **English**, **हिन्दी (Devanagari)**, or **Hinglish (Roman Hindi)** — for example: *'gehun me konsi khad dale'*, *'गेहूँ में खाद की मात्रा'*, or *'wheat fertilizer schedule'*.\n\nI dynamically generate answers line-by-line combining live **Google Gemini 2.0 Flash** with our verified ICAR agricultural research base. How may I help your farm today?",
      context_topics: ['AgriSmart Core Advisory', 'Trilingual Assistant'],
      engine: 'AgriSmart-Dual-Engine'
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [currentEngine, setCurrentEngine] = useState('Dynamic RAG + Gemini');
  const [isLiveGemini, setIsLiveGemini] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    const trimmed = (text || input).trim();
    if (!trimmed || loading) return;

    const userMsg = { role: 'user', content: trimmed };
    const history = messages
      .filter((_, i) => i > 0)
      .concat(userMsg)
      .map(m => ({ role: m.role, content: m.content }));

    // Add user message and empty model streaming placeholder
    const placeholderMsg = {
      role: 'model',
      content: '',
      context_topics: [],
      engine: 'Generating...',
      is_live_gemini: false,
      isStreaming: true
    };

    setMessages(prev => [...prev, userMsg, placeholderMsg]);
    setInput('');
    setLoading(true);

    let streamSuccess = false;

    // 1. Try real-time streaming endpoint first
    try {
      const response = await fetch(`${BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history: history.slice(-8) }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Streaming failed with status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulated = '';
      let streamTopics = [];
      let streamModel = 'AgriSmart';
      let liveGeminiActive = false;
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const ev of events) {
          const trimmedEv = ev.trim();
          if (!trimmedEv.startsWith('data: ')) continue;
          try {
            const parsed = JSON.parse(trimmedEv.substring(6));
            if (parsed.chunk) {
              accumulated += parsed.chunk;
              // Progressively update model message in real-time
              setMessages(prev => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last && last.role === 'model') {
                  next[next.length - 1] = {
                    ...last,
                    content: accumulated,
                    isStreaming: true
                  };
                }
                return next;
              });
            }
            if (parsed.done) {
              streamTopics = parsed.context_topics || [];
              streamModel = parsed.model || 'AgriSmart';
              liveGeminiActive = Boolean(parsed.is_live_gemini);
            }
          } catch (jsonErr) {
            // Ignore partial SSE JSON parse attempts
          }
        }
      }

      // Finalize the streamed message
      setMessages(prev => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last && last.role === 'model') {
          next[next.length - 1] = {
            ...last,
            content: accumulated || "Advisory generated successfully.",
            context_topics: streamTopics,
            engine: streamModel,
            is_live_gemini: liveGeminiActive,
            isStreaming: false
          };
        }
        return next;
      });

      setIsLiveGemini(liveGeminiActive);
      setCurrentEngine(streamModel);
      streamSuccess = true;

    } catch (streamErr) {
      console.warn("SSE stream failed, falling back to standard JSON API:", streamErr);
    }

    // 2. Fallback to standard chatWithAI if streaming did not complete
    if (!streamSuccess) {
      try {
        const res = await chatWithAI(trimmed, history);
        const data = res.data;

        setIsLiveGemini(Boolean(data.is_live_gemini));
        if (data.model) {
          setCurrentEngine(data.model);
        }

        setMessages(prev => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last && last.role === 'model') {
            next[next.length - 1] = {
              role: 'model',
              content: data.reply,
              context_topics: data.context_topics || [],
              engine: data.model || 'AgriSmart',
              is_live_gemini: data.is_live_gemini,
              notice: data.notice,
              isStreaming: false
            };
          }
          return next;
        });
      } catch (err) {
        const detail = err.response?.data?.detail;
        const errorMsg = typeof detail === 'object' ? (detail.message || JSON.stringify(detail)) : (detail || 'Connection error. Answering via local agricultural advisory.');

        setMessages(prev => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last && last.role === 'model') {
            next[next.length - 1] = {
              role: 'model', 
              content: `⚠️ ${errorMsg}\n\n*Please ensure the AgriSmart backend is running at http://localhost:8001.*`, 
              context_topics: [], 
              isError: true,
              isStreaming: false
            };
          }
          return next;
        });
      }
    }

    setLoading(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Simple Markdown text renderer for bold, lists, and headings
  const renderFormattedText = (text, isStreaming) => {
    if (!text && isStreaming) {
      return (
        <div className="flex items-center gap-2 text-xs text-gray-500 py-1">
          <CircularProgress size={14} color="inherit" />
          <span>Generating agricultural advisory...</span>
        </div>
      );
    }
    if (!text) return null;

    const lines = text.split('\n');
    return (
      <div>
        {lines.map((line, idx) => {
          let trimmed = line.trim();
          if (!trimmed) return <div key={idx} className="h-2" />;

          // Header 3
          if (trimmed.startsWith('### ')) {
            return <h4 key={idx} className="text-sm font-bold text-emerald-950 mt-2 mb-1">{trimmed.replace('### ', '')}</h4>;
          }
          // Divider
          if (trimmed === '---') {
            return <hr key={idx} className="my-2 border-gray-200" />;
          }
          // Bullet point
          if (trimmed.startsWith('• ') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            const itemText = trimmed.replace(/^[•\-\*]\s*/, '');
            return (
              <div key={idx} className="flex items-start gap-2 ml-1 text-xs sm:text-sm my-0.5">
                <span className="text-[#2B6049] font-bold">&bull;</span>
                <span dangerouslySetInnerHTML={{ __html: formatBold(itemText) }} />
              </div>
            );
          }
          // Italic notice
          if (trimmed.startsWith('*') && trimmed.endsWith('*')) {
            return (
              <p key={idx} className="text-[11px] text-gray-500 italic mt-1.5 leading-relaxed bg-white/60 p-2 rounded-lg border border-gray-200/50">
                {trimmed.replace(/^\*|\*$/g, '')}
              </p>
            );
          }
          // Standard paragraph
          return (
            <p key={idx} className="text-xs sm:text-sm my-1 leading-relaxed" dangerouslySetInnerHTML={{ __html: formatBold(trimmed) }} />
          );
        })}
        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-emerald-600 animate-pulse rounded-sm align-middle" />
        )}
      </div>
    );
  };

  const formatBold = (str) => {
    return str.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Main Chat Container */}
      <div className="bg-white rounded-3xl shadow-lg border border-gray-100 flex flex-col" style={{ height: 'calc(100vh - 240px)', minHeight: '540px' }}>
        
        {/* Header Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-b border-gray-200 rounded-t-3xl bg-gradient-to-r from-[#2B6049] to-[#1f3d32] text-white">
          <div className="flex items-center gap-3">
            <div className="bg-white/20 rounded-full p-2">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">AgriSmart Assistant</h2>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-white/20 px-2 py-0.5 rounded-full border border-white/20">
                  English • हिन्दी • Hinglish
                </span>
              </div>
              <p className="text-xs text-white/80">Gemini 2.0 Flash + Live Real-Time Token Generation</p>
            </div>
          </div>

          {/* Engine Status & Setup Button */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowKeyModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white/15 hover:bg-white/25 text-white transition border border-white/20"
              title="Configure Google Gemini API Key"
            >
              <Key className="w-3.5 h-3.5 text-amber-300" />
              <span>API Key Setup</span>
            </button>
            <div className="flex items-center gap-1.5 bg-black/25 px-3 py-1.5 rounded-xl border border-white/10 text-xs">
              <span className={`w-2 h-2 rounded-full ${isLiveGemini ? 'bg-emerald-400 animate-pulse' : 'bg-blue-400'}`} />
              <span className="font-semibold text-white/90">
                {isLiveGemini ? 'Gemini 2.0 Live' : 'Dynamic Knowledge Base'}
              </span>
            </div>
          </div>
        </div>

        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4 bg-gray-50/50">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'model' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#2B6049] flex items-center justify-center text-white shadow-sm mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}
              <div className={`max-w-[85%] rounded-2xl px-5 py-3.5 shadow-sm ${
                msg.role === 'user'
                  ? 'bg-[#2B6049] text-white rounded-br-sm'
                  : msg.isError
                    ? 'bg-red-50 border border-red-200 text-red-900 rounded-bl-sm'
                    : 'bg-white text-gray-800 border border-gray-200/80 rounded-bl-sm'
              }`}>
                {msg.role === 'user' ? (
                  <p className="text-sm font-medium whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div>
                    {renderFormattedText(msg.content, msg.isStreaming)}

                    {/* Context Topic Tags */}
                    {msg.context_topics?.length > 0 && !msg.isStreaming && (
                      <div className="mt-3 pt-2.5 border-t border-gray-100 flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">RAG Topics:</span>
                        {msg.context_topics.map((t, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-emerald-50 text-emerald-800 border border-emerald-100">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center shadow-sm mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>

        {/* Starter Questions Carousel / Pills */}
        <div className="px-4 py-2 bg-white border-t border-gray-100">
          <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1.5 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-[#2B6049]" /> Suggested Inquiries (English • हिन्दी • Hinglish)
          </p>
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {STARTER_QUESTIONS.map((sq, i) => (
              <button
                key={i}
                onClick={() => sendMessage(sq.query)}
                disabled={loading}
                className="whitespace-nowrap px-3 py-1.5 rounded-xl bg-gray-50 hover:bg-emerald-50 text-gray-700 hover:text-[#2B6049] text-xs font-semibold border border-gray-200/80 hover:border-emerald-200 transition active:scale-95 flex-shrink-0"
              >
                {sq.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <div className="p-3 sm:p-4 bg-white border-t border-gray-200 rounded-b-3xl">
          <div className="flex items-center gap-2 bg-gray-50 rounded-2xl px-4 py-2 border border-gray-200 focus-within:border-[#2B6049] focus-within:ring-2 focus-within:ring-emerald-100 transition">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask in English, हिन्दी, or Hinglish (e.g. Gehun me pehla pani kab de)..."
              disabled={loading}
              className="flex-1 bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none"
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="p-2.5 bg-[#2B6049] hover:bg-[#204a37] text-white rounded-xl shadow-md transition disabled:opacity-40 active:scale-95 flex items-center justify-center"
              title="Send Message"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Gemini API Key Setup Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 md:p-8 shadow-2xl border border-gray-100 space-y-5 animate-scale-up">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex items-center gap-2 text-[#2B6049]">
                <Key className="w-5 h-5 text-amber-500" />
                <h3 className="text-lg font-bold text-gray-800">Google Gemini API Key Setup</h3>
              </div>
              <button 
                onClick={() => setShowKeyModal(false)}
                className="text-gray-400 hover:text-gray-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs text-gray-600 space-y-3 leading-relaxed">
              <p>
                AgriSmart operates a <strong>Dual-Engine Architecture</strong>: it currently answers questions dynamically through our verified local agricultural knowledge base.
              </p>
              <p>
                To unlock live conversational generation via <strong>Google Gemini 2.0 Flash</strong>, follow these 5 steps:
              </p>
              
              <ol className="list-decimal list-inside space-y-2 font-medium text-gray-800 bg-gray-50 p-4 rounded-xl border border-gray-200">
                <li>
                  Open <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-emerald-700 underline font-bold inline-flex items-center gap-0.5">Google AI Studio <ExternalLink className="w-3 h-3" /></a>
                </li>
                <li>Sign in with your Google account and click <strong>"Create API key"</strong>.</li>
                <li>Copy your key (starts with <code className="bg-white px-1.5 py-0.5 rounded border border-gray-300 font-mono text-[11px]">AIzaSy...</code>).</li>
                <li>
                  Open file: <code className="bg-white px-1.5 py-0.5 rounded border border-gray-300 font-mono text-[11px]">CropYieldApp/CropYieldApp/backend/.env</code>
                </li>
                <li>
                  Update: <code className="bg-white px-1.5 py-0.5 rounded border border-gray-300 font-mono text-[11px]">GEMINI_API_KEY=your_copied_key</code>
                </li>
              </ol>

              <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-800 text-xs flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Dynamic Auto-Reload:</strong> Once saved in <code className="font-mono text-[11px]">backend/.env</code>, AgriSmart detects the key immediately without needing a server restart!
                </span>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowKeyModal(false)}
                className="px-6 py-2.5 bg-[#2B6049] text-white font-bold rounded-xl text-xs hover:bg-[#204a37] transition shadow-md"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
