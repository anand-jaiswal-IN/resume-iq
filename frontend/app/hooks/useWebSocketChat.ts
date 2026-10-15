import { useState, useEffect, useRef, useCallback } from "react";
import type { ChatMessage, IntentType, JobFitEvaluation } from "../lib/types";
import { api } from "../lib/api";

const WS_URL = typeof window !== "undefined"
  ? (window as any).__ENV__?.WS_URL || (import.meta as any).env?.VITE_WS_URL || "ws://localhost:8000/ws/chat"
  : process.env.WS_URL || "ws://localhost:8000/ws/chat";

export function useWebSocketChat(sessionId: string = "default", resumeId?: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  // Load session messages from backend when sessionId or resumeId changes
  useEffect(() => {
    let isCancelled = false;

    async function loadHistory() {
      if (resumeId && sessionId) {
        try {
          const detail = await api.getSessionDetail(resumeId, sessionId);
          if (!isCancelled) {
            if (detail && detail.messages && detail.messages.length > 0) {
              setMessages(
                detail.messages.map((m: any) => ({
                  id: m.id || `msg-${Math.random()}`,
                  role: m.role,
                  content: m.content,
                  timestamp: m.timestamp || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                  intent: m.intent,
                  jd_result: m.jd_result,
                }))
              );
              return;
            }
          }
        } catch {
          // If session doesn't exist on server yet, initialize with welcome prompt
        }
      }

      if (!isCancelled) {
        setMessages([
          {
            id: `welcome-${Date.now()}`,
            role: "assistant",
            content:
              "👋 Hello! I am **Resume IQ** — your interactive context-aware AI assistant.\n\n" +
              "Ask me anything about the candidate's skills, work experience, education, or projects. You can also evaluate a Job Description at any time.",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            intent: "GENERAL_CONVERSATION",
          },
        ]);
      }
    }

    loadHistory();

    return () => {
      isCancelled = true;
    };
  }, [sessionId, resumeId]);

  const connect = useCallback(() => {
    if (typeof window === "undefined") return;
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    try {
      const socket = new WebSocket(WS_URL);
      wsRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
        // Attempt reconnect after 3 seconds
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, 3000);
      };

      socket.onerror = () => {
        setIsConnected(false);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const type = payload.type;
          const content = payload.content;

          if (type === "intent") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant" && last.isStreaming) {
                last.intent = content as IntentType;
              }
              return updated;
            });
          } else if (type === "token") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant" && last.isStreaming) {
                last.content += content;
              }
              return updated;
            });
          } else if (type === "jd_result") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                last.jd_result = content as JobFitEvaluation;
              }
              return updated;
            });
          } else if (type === "done") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                last.isStreaming = false;
                if (!last.content && typeof content === "string") {
                  last.content = content;
                }
              }
              return updated;
            });
            setIsGenerating(false);
          } else if (type === "error") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                last.content += `\n\n❌ *Error: ${content}*`;
                last.isStreaming = false;
              }
              return updated;
            });
            setIsGenerating(false);
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };
    } catch (err) {
      console.error("Failed to establish WebSocket connection:", err);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim() || isGenerating) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsGenerating(true);

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            message: text,
            session_id: sessionId,
            resume_id: resumeId || undefined,
          })
        );
      } else {
        // Fallback to REST
        api
          .sendChatMessage(text, sessionId, resumeId || undefined)
          .then((res) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                last.content = res.answer;
                last.intent = res.intent;
                last.jd_result = res.jd_evaluation;
                last.isStreaming = false;
              }
              return updated;
            });
            setIsGenerating(false);
          })
          .catch((err) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                last.content = `❌ Connection error: ${err.message || "Failed to reach backend"}`;
                last.isStreaming = false;
              }
              return updated;
            });
            setIsGenerating(false);
          });
      }
    },
    [isGenerating, sessionId, resumeId]
  );

  const clearChat = useCallback(async () => {
    try {
      await api.clearHistory(sessionId);
    } catch (err) {
      console.warn("Could not clear server session:", err);
    }
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: "assistant",
        content: "Conversation cleared. Ask me anything about this candidate's resume!",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        intent: "GENERAL_CONVERSATION",
      },
    ]);
  }, [sessionId]);

  return {
    messages,
    sendMessage,
    clearChat,
    setMessages,
    isConnected,
    isGenerating,
  };
}
