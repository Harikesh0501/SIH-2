"use client";

import React, { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import {
  Send,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  RotateCcw,
  BookOpen,
  Copy,
  Check,
  User,
  ArrowRight
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL, apiPost } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/Card";
import { Breadcrumbs } from "@/components/Breadcrumbs";

interface ChatMessage {
  id: string;
  sender: "USER" | "ASSISTANT";
  text: string;
  voice_ready_text?: string;
  language: "en" | "hi";
  citations?: Array<{
    title: string;
    chapter?: string;
    clause?: string;
    section?: string;
    relevance?: number;
  }>;
  timestamp: string;
}

const DEFAULT_PROMPTS = [
  {
    en: "Explain GVA at basic prices vs GDP at market prices.",
    hi: "मूल कीमतों पर GVA और बाजार मूल्यों पर GDP में क्या अंतर है?",
    category: "National Accounts"
  },
  {
    en: "How are elementary price aggregates calculated in CPI?",
    hi: "उपभोक्ता मूल्य सूचकांक (CPI) में प्राथमिक एकत्रीकरण कैसे किया जाता है?",
    category: "Price Indices"
  },
  {
    en: "What is the difference between UPS and Subsidiary Status?",
    hi: "सामान्य प्रमुख स्थिति (UPS) और सहायक स्थिति में क्या अंतर है?",
    category: "Labour Statistics"
  },
  {
    en: "What are the core dimensions of data quality?",
    hi: "डेटा गुणवत्ता के मुख्य आयाम कौन से हैं?",
    category: "Data Quality"
  }
];

export default function ChatPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-sm text-zinc-500">Loading AI Tutor...</div>}>
      <ChatContent />
    </React.Suspense>
  );
}

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("query") || "";
  const { currentUser, activePersona } = useAuth();

  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState(initialQuery);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(`session-${Date.now()}`);

  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = language === "hi" ? "hi-IN" : "en-IN";

        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInputMessage(transcript);
          setIsListening(false);
        };

        recognition.onerror = () => {
          setIsListening(false);
        };

        recognition.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current = recognition;
      }
    }
  }, [language]);

  useEffect(() => {
    setMessages([
      {
        id: "msg-welcome",
        sender: "ASSISTANT",
        text:
          language === "en"
            ? `Hello ${currentUser?.full_name || activePersona?.name || "there"}! I am Sankhyiki Mitra, your AI Statistical Tutor.\n\nHow can I help you today?`
            : `नमस्ते ${currentUser?.full_name || activePersona?.name || ""}! मैं सांख्यिकी मित्र हूँ, आपका AI सांख्यिकी शिक्षक।\n\nआज मैं आपकी क्या मदद कर सकता हूँ?`,
        language,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      }
    ]);
  }, [language, currentUser, activePersona]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleToggleVoiceInput = () => {
    if (!recognitionRef.current) return;
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.lang = language === "hi" ? "hi-IN" : "en-IN";
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleSpeak = (text?: string) => {
    if (!text || typeof window === "undefined" || !("speechSynthesis" in window)) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const cleanText = text.replace(/[*#_`\\]/g, "");
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = language === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = 0.95;

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const handleSendMessage = async (msgText?: string) => {
    const query = msgText || inputMessage;
    if (!query.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "USER",
      text: query,
      language,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const res = await apiPost<any>("/chat/message", {
        message: query,
        session_id: sessionId,
        language
      });

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: "ASSISTANT",
        text: res.content || res.response || "No response received.",
        voice_ready_text: res.content || res.response,
        language: res.language || language,
        citations: (res.sources || res.citations || []).map((s: any) => ({
          title: s.source || s.title || "MoSPI Manual",
          chapter: s.section || s.chapter,
          clause: s.clause,
          relevance: s.relevance_score || s.relevance,
        })),
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const fallbackResponse =
        language === "en"
          ? `I'm unable to connect to the server right now, but here is some general information about your query. Please try again later for more specific details.`
          : `मैं अभी सर्वर से कनेक्ट करने में असमर्थ हूँ, लेकिन यहाँ आपके प्रश्न के बारे में कुछ सामान्य जानकारी है। कृपया अधिक विशिष्ट विवरण के लिए बाद में पुनः प्रयास करें।`;

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: "ASSISTANT",
        text: fallbackResponse,
        language,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleResetChat = async () => {
    try {
      await fetch(`${API_BASE_URL}/chat/history?session_id=${sessionId}`, {
        method: "DELETE"
      });
    } catch (e) {}

    setMessages([
      {
        id: "msg-welcome",
        sender: "ASSISTANT",
        text:
          language === "en"
            ? "Conversation reset. You may ask a new question."
            : "बातचीत रीसेट हो गई है। आप एक नया प्रश्न पूछ सकते हैं।",
        language,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      }
    ]);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-6 px-4">
      <Breadcrumbs items={[{ label: "AI Tutor" }]} />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-zinc-900">
            Sankhyiki Mitra
          </h1>
          <p className="text-sm text-zinc-500">
            Your AI Statistical Tutor
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="inline-flex rounded-md border border-zinc-200 p-1 bg-zinc-50">
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={`px-3 py-1.5 text-xs rounded-sm font-medium transition-colors ${
                language === "en"
                  ? "bg-white text-zinc-900 shadow-sm border border-zinc-200"
                  : "text-zinc-500 hover:text-zinc-900"
              }`}
            >
              EN
            </button>
            <button
              type="button"
              onClick={() => setLanguage("hi")}
              className={`px-3 py-1.5 text-xs rounded-sm font-medium transition-colors ${
                language === "hi"
                  ? "bg-white text-zinc-900 shadow-sm border border-zinc-200"
                  : "text-zinc-500 hover:text-zinc-900"
              }`}
            >
              HI
            </button>
          </div>

          <button
            type="button"
            onClick={handleResetChat}
            className="p-2 rounded-md border border-zinc-200 bg-white text-zinc-600 hover:bg-zinc-50 transition-colors"
            title="Reset Conversation"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {DEFAULT_PROMPTS.map((item, idx) => {
          const promptText = language === "en" ? item.en : item.hi;
          return (
            <button
              key={idx}
              type="button"
              onClick={() => handleSendMessage(promptText)}
              className="px-4 py-2 rounded-full border border-zinc-200 bg-white hover:border-zinc-400 text-xs text-zinc-700 transition-colors flex items-center gap-2"
            >
              <span>{promptText}</span>
              <ArrowRight className="w-3 h-3 text-zinc-400" />
            </button>
          );
        })}
      </div>

      <Card className="border-zinc-200 flex flex-col h-[600px] overflow-hidden rounded-xl">
        <CardContent className="flex-1 overflow-y-auto p-6 space-y-6 bg-zinc-50/50">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-end gap-2 ${
                msg.sender === "USER" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.sender === "ASSISTANT" && (
                <div className="w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-xs shrink-0 mb-1">
                  SM
                </div>
              )}

              <div
                className={`max-w-[75%] rounded-2xl p-4 text-sm ${
                  msg.sender === "USER"
                    ? "bg-zinc-100 text-zinc-900 rounded-br-none"
                    : "bg-white border border-zinc-200 text-zinc-900 rounded-bl-none shadow-sm"
                }`}
              >
                <div className="whitespace-pre-line leading-relaxed">
                  {msg.text}
                </div>

                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-zinc-100 space-y-2">
                    <div className="flex items-center gap-1.5 text-xs font-medium text-zinc-500">
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>References</span>
                    </div>
                    <div className="space-y-1.5">
                      {msg.citations.map((c, cIdx) => (
                        <div
                          key={cIdx}
                          className="p-2 rounded-md bg-zinc-50 border border-zinc-100 text-xs text-zinc-600"
                        >
                          <div className="font-medium text-zinc-800">{c.title}</div>
                          {c.chapter && <div className="text-zinc-500 mt-0.5">{c.chapter} {c.clause ? `• ${c.clause}` : ""}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {msg.sender === "ASSISTANT" && (
                  <div className="mt-3 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleSpeak(msg.voice_ready_text || msg.text)}
                      className="text-zinc-400 hover:text-zinc-700 transition-colors"
                    >
                      {isSpeaking ? (
                        <VolumeX className="w-4 h-4 text-zinc-900" />
                      ) : (
                        <Volume2 className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleCopy(msg.id, msg.text)}
                      className="text-zinc-400 hover:text-zinc-700 transition-colors"
                    >
                      {copiedId === msg.id ? (
                        <Check className="w-4 h-4 text-black" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                )}
              </div>

              {msg.sender === "USER" && (
                <div className="w-8 h-8 rounded-full bg-zinc-200 text-zinc-600 flex items-center justify-center mb-1 shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex items-end gap-2 justify-start">
              <div className="w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-xs shrink-0 mb-1">
                SM
              </div>
              <div className="bg-white border border-zinc-200 rounded-2xl rounded-bl-none p-4 shadow-sm">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-zinc-300"></div>
                  <div className="w-2 h-2 rounded-full bg-zinc-400"></div>
                  <div className="w-2 h-2 rounded-full bg-zinc-500"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>

        <div className="p-4 bg-white border-t border-zinc-200">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-3"
          >
            <button
              type="button"
              onClick={handleToggleVoiceInput}
              className={`p-3 rounded-full border transition-colors ${
                isListening
                  ? "bg-zinc-100 border-zinc-300 text-black"
                  : "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50"
              }`}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={isListening ? "Listening..." : "Message Sankhyiki Mitra..."}
              className="flex-1 text-sm px-4 py-3 rounded-full border border-zinc-200 focus:outline-none focus:border-zinc-400 focus:ring-1 focus:ring-zinc-400 bg-zinc-50"
            />

            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="p-3 bg-black text-white rounded-full hover:bg-zinc-800 disabled:opacity-50 transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </Card>
    </div>
  );
}
