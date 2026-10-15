import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import {
  Send,
  Trash2,
  Sparkles,
  Bot,
  User,
  Briefcase,
  FileText,
  Search,
  Plus,
} from "lucide-react";
import { useWebSocketChat } from "../../hooks/useWebSocketChat";
import { chatInputSchema } from "../../lib/validations";
import type { ChatMessage, IntentType } from "../../lib/types";

interface ChatContainerProps {
  activeResumeId?: string | null;
  activeResumeName?: string | null;
  activeSessionId?: string;
  activeSessionTitle?: string;
  onOpenJdTab?: (sampleJd?: string) => void;
  onNewSession?: () => void;
  onDeleteSession?: (sessionId: string) => void;
}

const QUICK_PROMPTS = [
  "What are the candidate's top technical skills?",
  "Tell me about the candidate's key projects",
  "Summarize the candidate's career experience",
  "What is the candidate's education and degrees?",
  "Does the candidate have AI/ML and RAG experience?",
  "Evaluate candidate fit for a Senior Full-Stack role",
];

export const ChatContainer: React.FC<ChatContainerProps> = ({
  activeResumeId,
  activeResumeName,
  activeSessionId = "default",
  activeSessionTitle = "Chat Session",
  onOpenJdTab,
  onNewSession,
  onDeleteSession,
}) => {
  const { messages, sendMessage, clearChat, isGenerating, isConnected } = useWebSocketChat(
    activeSessionId,
    activeResumeId
  );
  const [inputText, setInputText] = useState("");
  const [inputError, setInputError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    setInputError(null);
    const result = chatInputSchema.safeParse(inputText);
    if (!result.success) {
      setInputError(result.error.issues[0]?.message || "Invalid input");
      return;
    }
    sendMessage(result.data);
    setInputText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getIntentBadge = (intent?: IntentType) => {
    if (!intent) return null;
    switch (intent) {
      case "FACTUAL_QA":
        return (
          <span className="inline-flex items-center gap-1 rounded-full text-[11px] font-semibold uppercase tracking-[0.88px] px-2.5 py-0.5 bg-[#9fbbe0]/20 text-[#26251e]">
            <Search className="w-3 h-3" /> Factual RAG
          </span>
        );
      case "JD_EVALUATION":
        return (
          <span className="inline-flex items-center gap-1 rounded-full text-[11px] font-semibold uppercase tracking-[0.88px] px-2.5 py-0.5 bg-[#c0a8dd]/20 text-[#26251e]">
            <Briefcase className="w-3 h-3" /> JD Match
          </span>
        );
      case "RESUME_SUMMARY":
        return (
          <span className="inline-flex items-center gap-1 rounded-full text-[11px] font-semibold uppercase tracking-[0.88px] px-2.5 py-0.5 bg-[#9fc9a2]/20 text-[#26251e]">
            <FileText className="w-3 h-3" /> Summary
          </span>
        );
      case "GENERAL_CONVERSATION":
        return (
          <span className="inline-flex items-center gap-1 rounded-full text-[11px] font-semibold uppercase tracking-[0.88px] px-2.5 py-0.5 bg-[#dfa88f]/20 text-[#26251e]">
            <Sparkles className="w-3 h-3" /> Assistant
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-[740px] rounded-xl bg-white border border-[#e6e5e0] overflow-hidden">
      {/* Chat Header Bar */}
      <div className="bg-[#fafaf7] px-5 py-3 border-b border-[#e6e5e0] flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-white border border-[#e6e5e0] flex items-center justify-center p-1 flex-shrink-0 shadow-2xs">
            <img src="/favicon.ico" alt="Resume IQ" className="w-full h-full object-contain" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold tracking-tight text-[#26251e] truncate">
                {activeSessionTitle}
              </h2>
              {activeResumeName && (
                <span className="text-[11px] font-normal text-[#807d72] hidden sm:inline truncate">
                  ({activeResumeName})
                </span>
              )}
              <span
                className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  isConnected ? "bg-[#1f8a65]" : "bg-amber-400 animate-pulse"
                }`}
                title={isConnected ? "Real-time stream ready" : "Connecting..."}
              />
            </div>
            <p className="text-[11px] text-[#807d72]">
              Multi-turn conversational RAG with Gemini
            </p>
          </div>
        </div>

        {/* Header Session Actions */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {onNewSession && (
            <button
              type="button"
              onClick={onNewSession}
              className="inline-flex items-center gap-1 px-2.5 py-1 bg-white border border-[#e6e5e0] hover:border-[#cfcdc4] text-[#26251e] text-xs font-medium rounded-md transition-colors cursor-pointer"
            >
              <Plus className="w-3 h-3" />
              <span className="hidden sm:inline">New Session</span>
            </button>
          )}

          {onDeleteSession && activeSessionId && (
            <button
              type="button"
              onClick={() => onDeleteSession(activeSessionId)}
              title="Delete this session"
              className="p-1.5 text-[#807d72] hover:text-[#cf2d56] transition-colors rounded-md cursor-pointer hover:bg-[#cf2d56]/10"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Message Thread */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-[85%] ${
              msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
            }`}
          >
            {/* Avatar */}
            <div
              className={`w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-xs overflow-hidden ${
                msg.role === "user"
                  ? "bg-[#26251e] text-white"
                  : "bg-white border border-[#e6e5e0] p-1"
              }`}
            >
              {msg.role === "user" ? (
                <User className="w-3.5 h-3.5" />
              ) : (
                <img src="/favicon.ico" alt="Resume IQ" className="w-full h-full object-contain" />
              )}
            </div>

            {/* Bubble */}
            <div className="flex flex-col gap-1">
              {/* Header meta */}
              <div
                className={`flex items-center gap-2 text-[11px] text-[#a09c92] px-1 ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <span>{msg.role === "user" ? "You" : "Assistant"}</span>
                <span>•</span>
                <span>{msg.timestamp}</span>
                {msg.role === "assistant" && getIntentBadge(msg.intent)}
              </div>

              {/* Message Content */}
              <div
                className={`px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-[#26251e] text-white rounded-2xl rounded-tr-none"
                    : "bg-[#fafaf7] text-[#26251e] rounded-2xl rounded-tl-none border border-[#e6e5e0]"
                }`}
              >
                {msg.content ? (
                  <div
                    className={
                      msg.role === "user"
                        ? "prose prose-invert max-w-none text-sm break-words [&>p]:mb-2 [&>p:last-child]:mb-0 [&>ul]:list-disc [&>ul]:pl-4 [&>ul]:my-2 [&>li]:mb-1 [&>code]:bg-white/10 [&>code]:text-white [&>code]:px-1 [&>code]:py-0.5 [&>code]:rounded"
                        : "prose max-w-none text-sm break-words text-[#26251e] [&>p]:mb-2 [&>p:last-child]:mb-0 [&>ul]:list-disc [&>ul]:pl-4 [&>ul]:my-2 [&>li]:mb-1 [&>h3]:text-base [&>h3]:font-medium [&>h3]:text-[#26251e] [&>h4]:text-sm [&>h4]:font-medium [&>h4]:text-[#26251e] [&>code]:bg-[#e6e5e0] [&>code]:text-[#26251e] [&>code]:px-1 [&>code]:py-0.5 [&>code]:rounded [&>strong]:font-semibold [&>strong]:text-[#26251e] [&>a]:text-[#f54e00] [&>a]:underline"
                    }
                  >
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-[#807d72] py-1">
                    <span className="w-2 h-2 rounded-full bg-[#807d72] animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 rounded-full bg-[#807d72] animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 rounded-full bg-[#807d72] animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                )}

                {/* Embedded Scorecard Badge if JD Result Present */}
                {msg.jd_result && (
                  <div className="mt-3 pt-3 border-t border-[#e6e5e0] flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-[#f54e00]">
                        Fit Score: {msg.jd_result.fit_score}%
                      </span>
                      <span className="text-xs text-[#807d72]">({msg.jd_result.verdict})</span>
                    </div>
                    {onOpenJdTab && (
                      <button
                        type="button"
                        onClick={() => onOpenJdTab()}
                        className="bg-white border border-[#cfcdc4] text-[#26251e] rounded-lg text-xs px-2.5 py-1 hover:bg-[#fafaf7] transition-colors cursor-pointer"
                      >
                        View Full Scorecard
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="px-4 py-2 bg-[#fafaf7] border-t border-[#e6e5e0] flex gap-2 overflow-x-auto no-scrollbar">
        {QUICK_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => {
              setInputText(prompt);
              sendMessage(prompt);
            }}
            disabled={isGenerating}
            className="text-xs whitespace-nowrap px-3 py-1.5 rounded-full bg-white border border-[#e6e5e0] text-[#5a5852] hover:border-[#f54e00] hover:text-[#f54e00] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <div className="p-4 bg-white border-t border-[#e6e5e0]">
        <div className="flex items-end gap-2 bg-[#fafaf7] rounded-xl border border-[#e6e5e0] p-3 focus-within:border-[#f54e00] focus-within:ring-1 focus-within:ring-[#f54e00]/20 transition-all">
          <textarea
            value={inputText}
            onChange={(e) => {
              setInputText(e.target.value);
              if (inputError) setInputError(null);
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              activeResumeName
                ? `Ask about ${activeResumeName}'s experience, skills, projects, or paste a JD...`
                : "Ask about candidate's skills, projects, experience, or paste a JD..."
            }
            rows={2}
            className="flex-1 bg-transparent resize-none border-none outline-none text-sm text-[#26251e] placeholder-[#807d72] p-1"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!inputText.trim() || isGenerating}
            aria-label="Send message"
            className="w-10 h-10 rounded-lg bg-[#f54e00] text-white flex items-center justify-center hover:bg-[#d04200] disabled:opacity-40 disabled:hover:bg-[#f54e00] disabled:cursor-not-allowed transition-colors cursor-pointer flex-shrink-0"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
        {inputError && (
          <div className="text-xs text-[#cf2d56] mt-1.5 ml-2 font-normal">
            {inputError}
          </div>
        )}
      </div>
    </div>
  );
};
