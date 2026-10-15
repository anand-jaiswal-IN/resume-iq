import React, { useState, useEffect, useCallback } from "react";
import type { Route } from "./+types/home";
import { Navbar } from "../components/layout/Navbar";
import { ResumeListPanel } from "../components/dashboard/ResumeListPanel";
import { SessionListPanel } from "../components/dashboard/SessionListPanel";
import { ChatContainer } from "../components/chat/ChatContainer";
import { JDEvaluatorView } from "../components/jd-matcher/JDEvaluatorView";
import { CandidateProfileView } from "../components/profile/CandidateProfileView";
import { ResumeUploadModal } from "../components/upload/ResumeUploadModal";
import { api } from "../lib/api";
import type { ResumeItem, ChatSessionSummary, ResumeStatus } from "../lib/types";
import { FileText, Upload, Calendar, Layers, Database } from "lucide-react";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Resume IQ — Context-Aware AI Resume Bot" },
    {
      name: "description",
      content:
        "Resume IQ: Context-Aware AI Resume Bot with Multi-Resume Indexing, Persistent Chat Sessions, and Job Description Fit Evaluation.",
    },
  ];
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "jd" | "profile">("chat");
  const [isBackendHealthy, setIsBackendHealthy] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  // Resume state
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [activeResumeId, setActiveResumeId] = useState<string | null>(null);
  const [isLoadingResumes, setIsLoadingResumes] = useState(true);

  // Session state
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("default");
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Active resume object
  const activeResume = resumes.find((r) => r.id === activeResumeId) || resumes[0] || null;

  // Adapt active resume to ResumeStatus for backward compatibility with Navbar/other views
  const resumeStatus: ResumeStatus | null = activeResume
    ? {
        is_loaded: true,
        file_name: activeResume.file_name,
        candidate_name: activeResume.candidate_name,
        headline: activeResume.headline,
        total_chunks: activeResume.total_chunks,
        total_links: activeResume.links_count,
        active_resume_id: activeResume.id,
        total_resumes: resumes.length,
      }
    : null;

  // 1. Fetch Health
  const checkHealth = useCallback(async () => {
    try {
      const healthRes = await api.getHealth();
      setIsBackendHealthy(healthRes.status === "ok");
    } catch {
      setIsBackendHealthy(false);
    }
  }, []);

  // 2. Fetch all indexed resumes from backend
  const loadResumes = useCallback(async (selectNewestId?: string) => {
    setIsLoadingResumes(true);
    try {
      const res = await api.getResumes();
      const list = res.resumes || [];
      setResumes(list);

      if (list.length > 0) {
        let targetId = selectNewestId;
        if (!targetId) {
          const activeItem = list.find((r) => r.is_active);
          targetId = activeItem ? activeItem.id : list[0].id;
        }
        setActiveResumeId(targetId);
      } else {
        setActiveResumeId(null);
        setSessions([]);
      }
    } catch (err) {
      console.error("Failed to load resumes from backend:", err);
      setResumes([]);
      setActiveResumeId(null);
    } finally {
      setIsLoadingResumes(false);
    }
  }, []);

  // 3. Fetch sessions for the active resume
  const loadSessions = useCallback(async (resumeId: string) => {
    if (!resumeId) return;
    setIsLoadingSessions(true);
    try {
      const sessList = await api.getResumeSessions(resumeId);
      setSessions(sessList);

      if (sessList.length > 0) {
        setActiveSessionId((curr) => {
          const exists = sessList.some((s) => s.id === curr);
          return exists ? curr : sessList[0].id;
        });
      } else {
        // Automatically create a default first session for this resume
        try {
          const newSess = await api.createResumeSession(resumeId, "Initial Chat");
          const summaryItem: ChatSessionSummary = {
            id: newSess.id,
            resume_id: newSess.resume_id,
            title: newSess.title,
            created_at: newSess.created_at,
            updated_at: newSess.updated_at,
            message_count: newSess.messages?.length || 0,
          };
          setSessions([summaryItem]);
          setActiveSessionId(newSess.id);
        } catch {
          setActiveSessionId("default");
        }
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
      setSessions([]);
      setActiveSessionId("default");
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    checkHealth();
    loadResumes();

    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, [checkHealth, loadResumes]);

  // Load sessions whenever activeResumeId changes
  useEffect(() => {
    if (activeResumeId) {
      loadSessions(activeResumeId);
    }
  }, [activeResumeId, loadSessions]);

  // Handlers for Resume operations
  const handleSelectResume = async (resumeId: string) => {
    if (resumeId === activeResumeId) return;
    setActiveResumeId(resumeId);

    // Update local active indicator
    setResumes((prev) =>
      prev.map((r) => ({
        ...r,
        is_active: r.id === resumeId,
      }))
    );

    // Sync active collection in backend
    try {
      await api.activateResume(resumeId);
    } catch (err) {
      console.error("Failed to activate resume in backend:", err);
    }
  };

  const handleDeleteResume = async (resumeId: string) => {
    try {
      await api.deleteResume(resumeId);
      const remaining = resumes.filter((r) => r.id !== resumeId);
      setResumes(remaining);

      if (activeResumeId === resumeId) {
        const nextActive = remaining.find((r) => r.is_active) || remaining[0] || null;
        setActiveResumeId(nextActive ? nextActive.id : null);
      }
    } catch (err) {
      console.error("Failed to delete resume:", err);
    }
  };

  // Handlers for Session operations
  const handleCreateSession = async () => {
    if (!activeResumeId) return;
    try {
      const nextNum = sessions.length + 1;
      const newSess = await api.createResumeSession(activeResumeId, `Chat Session ${nextNum}`);
      const summaryItem: ChatSessionSummary = {
        id: newSess.id,
        resume_id: newSess.resume_id,
        title: newSess.title,
        created_at: newSess.created_at,
        updated_at: newSess.updated_at,
        message_count: newSess.messages?.length || 0,
      };
      setSessions((prev) => [summaryItem, ...prev]);
      setActiveSessionId(newSess.id);
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!activeResumeId) return;
    try {
      await api.deleteResumeSession(activeResumeId, sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);

      if (activeSessionId === sessionId) {
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].id);
        } else {
          // If all sessions deleted, create a fresh one
          handleCreateSession();
        }
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  const handleUploadSuccess = () => {
    loadResumes();
    setActiveTab("chat");
  };

  // Active session title
  const activeSessionTitle =
    sessions.find((s) => s.id === activeSessionId)?.title || "Chat Session";

  return (
    <div className="min-h-screen bg-[#f7f7f4] text-[#26251e] flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar
        resumeStatus={resumeStatus}
        onOpenUpload={() => setIsUploadOpen(true)}
        isBackendHealthy={isBackendHealthy}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
      />

      <main className="max-w-[1340px] mx-auto w-full px-4 sm:px-6 py-6 flex-1 flex flex-col gap-6">
        {/* TAB 1: DASHBOARD & CHAT */}
        {activeTab === "chat" && (
          <div className="flex-1 flex flex-col gap-6">
            {/* When no resumes are indexed at all */}
            {!isLoadingResumes && resumes.length === 0 ? (
              <div className="flex-1 flex items-center justify-center py-16">
                <div className="bg-white rounded-xl border border-[#e6e5e0] p-10 max-w-lg w-full text-center flex flex-col items-center">
                  <div className="w-12 h-12 rounded-xl bg-[#fafaf7] border border-[#e6e5e0] flex items-center justify-center text-[#26251e] mb-4">
                    <FileText className="w-6 h-6" />
                  </div>
                  <h2 className="text-xl font-normal tracking-tight text-[#26251e]">
                    No Resumes Uploaded Yet
                  </h2>
                  <p className="text-sm text-[#5a5852] mt-2 leading-relaxed">
                    Upload your first candidate PDF resume to automatically index its
                    skills, experience, and projects into ChromaDB for real-time RAG chat.
                  </p>
                  <button
                    type="button"
                    onClick={() => setIsUploadOpen(true)}
                    className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 bg-[#f54e00] hover:bg-[#d04200] text-white text-sm font-medium rounded-lg transition-colors cursor-pointer"
                  >
                    <Upload className="w-4 h-4" />
                    <span>Upload First Resume</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                {/* Left Column: Dashboard Sidebar with Resumes and Chat Sessions (4 cols) */}
                <div className="lg:col-span-4 flex flex-col gap-4">
                  {/* Resumes Panel */}
                  <ResumeListPanel
                    resumes={resumes}
                    activeResumeId={activeResumeId}
                    onSelectResume={handleSelectResume}
                    onDeleteResume={handleDeleteResume}
                    onOpenUpload={() => setIsUploadOpen(true)}
                    isLoading={isLoadingResumes}
                  />

                  {/* Sessions Panel for Current Resume */}
                  <SessionListPanel
                    sessions={sessions}
                    activeSessionId={activeSessionId}
                    onSelectSession={setActiveSessionId}
                    onCreateSession={handleCreateSession}
                    onDeleteSession={handleDeleteSession}
                    isLoading={isLoadingSessions}
                  />
                </div>

                {/* Right Column: Active Candidate Quick Bar + Chat Interface (8 cols) */}
                <div className="lg:col-span-8 flex flex-col gap-4">
                  {/* Active Candidate Spotlight Bar */}
                  {activeResume && (
                    <div className="p-4 rounded-xl bg-white border border-[#e6e5e0] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72]">
                            Active Candidate
                          </span>
                          <span className="text-xs text-[#cfcdc4]">•</span>
                          <span className="text-xs text-[#5a5852] truncate font-mono">
                            {activeResume.file_name}
                          </span>
                        </div>
                        <h1 className="text-lg font-normal tracking-tight text-[#26251e] truncate mt-0.5">
                          {activeResume.candidate_name || "Candidate Profile"}
                        </h1>
                        {activeResume.headline && (
                          <p className="text-xs text-[#5a5852] truncate mt-0.5">
                            {activeResume.headline}
                          </p>
                        )}
                      </div>

                      {/* Metadata Badges */}
                      <div className="flex flex-wrap items-center gap-2 flex-shrink-0">
                        <span className="px-2.5 py-1 rounded-full bg-[#f7f7f4] border border-[#e6e5e0] text-[#26251e] text-[11px] font-medium">
                          {activeResume.total_chunks || 0} Chunks
                        </span>
                        <span className="px-2.5 py-1 rounded-full bg-[#f7f7f4] border border-[#e6e5e0] text-[#26251e] text-[11px] font-medium">
                          ChromaDB RAG
                        </span>
                        <span className="px-2.5 py-1 rounded-full bg-[#f7f7f4] border border-[#e6e5e0] text-[#26251e] text-[11px] font-medium">
                          Gemini 2.5 Flash
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Chat Container with persistent session support */}
                  <ChatContainer
                    activeResumeId={activeResumeId}
                    activeResumeName={activeResume?.candidate_name || activeResume?.file_name}
                    activeSessionId={activeSessionId}
                    activeSessionTitle={activeSessionTitle}
                    onOpenJdTab={() => setActiveTab("jd")}
                    onNewSession={handleCreateSession}
                    onDeleteSession={handleDeleteSession}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: JOB DESCRIPTION FIT EVALUATOR */}
        {activeTab === "jd" && (
          <div className="flex-1 flex flex-col gap-4">
            {activeResume && (
              <div className="p-4 rounded-xl bg-white border border-[#e6e5e0] flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72]">
                    Evaluating Against
                  </span>
                  <p className="text-base font-normal tracking-tight text-[#26251e]">
                    {activeResume.candidate_name || activeResume.file_name}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveTab("chat")}
                  className="text-xs text-[#f54e00] hover:underline font-medium cursor-pointer"
                >
                  Switch Resume
                </button>
              </div>
            )}
            <JDEvaluatorView
              activeResumeId={activeResumeId}
              activeResumeName={activeResume?.candidate_name || activeResume?.file_name}
            />
          </div>
        )}

        {/* TAB 3: CANDIDATE PROFILE */}
        {activeTab === "profile" && (
          <div className="flex-1 flex flex-col gap-4">
            {activeResume && (
              <div className="p-4 rounded-xl bg-white border border-[#e6e5e0] flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72]">
                    Profile Dossier
                  </span>
                  <p className="text-base font-normal tracking-tight text-[#26251e]">
                    {activeResume.candidate_name || activeResume.file_name}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveTab("chat")}
                  className="text-xs text-[#f54e00] hover:underline font-medium cursor-pointer"
                >
                  Back to Dashboard
                </button>
              </div>
            )}
            <CandidateProfileView activeResumeId={activeResumeId} />
          </div>
        )}
      </main>

      {/* Upload Resume Modal */}
      <ResumeUploadModal
        open={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
}
