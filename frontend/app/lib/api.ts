import axios from "axios";
import type {
  ResumeStatus,
  ResumeItem,
  ResumeListResponse,
  CandidateProfile,
  JobFitEvaluation,
  SummaryResponse,
  LinksResponse,
  HealthResponse,
  StatsResponse,
  UploadResumeResponse,
  ChatSessionSummary,
  ChatSessionDetail,
} from "./types";

const API_BASE_URL = typeof window !== "undefined"
  ? (window as any).__ENV__?.API_BASE_URL || "http://localhost:8000"
  : "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 45000,
});

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await apiClient.get<HealthResponse>("/api/health");
    return res.data;
  },

  async getStats(): Promise<StatsResponse> {
    const res = await apiClient.get<StatsResponse>("/api/stats");
    return res.data;
  },

  // ── Multi-Resume Management ──────────────────────────────────────────────────

  async getResumes(): Promise<ResumeListResponse> {
    const res = await apiClient.get<ResumeListResponse>("/api/resumes");
    return res.data;
  },

  async activateResume(resumeId: string): Promise<any> {
    const res = await apiClient.post(`/api/resumes/${resumeId}/activate`);
    return res.data;
  },

  async deleteResume(resumeId: string): Promise<any> {
    const res = await apiClient.delete(`/api/resumes/${resumeId}`);
    return res.data;
  },

  // ── Chat Sessions per Resume ─────────────────────────────────────────────────

  async getResumeSessions(resumeId: string): Promise<ChatSessionSummary[]> {
    const res = await apiClient.get<ChatSessionSummary[]>(`/api/resumes/${resumeId}/sessions`);
    return res.data;
  },

  async createResumeSession(resumeId: string, title?: string): Promise<ChatSessionDetail> {
    const res = await apiClient.post<ChatSessionDetail>(`/api/resumes/${resumeId}/sessions`, {
      title,
    });
    return res.data;
  },

  async getSessionDetail(resumeId: string, sessionId: string): Promise<ChatSessionDetail> {
    const res = await apiClient.get<ChatSessionDetail>(`/api/resumes/${resumeId}/sessions/${sessionId}`);
    return res.data;
  },

  async deleteResumeSession(resumeId: string, sessionId: string): Promise<any> {
    const res = await apiClient.delete(`/api/resumes/${resumeId}/sessions/${sessionId}`);
    return res.data;
  },

  // ── Resume Profile & Ingestion ───────────────────────────────────────────────

  async getResumeStatus(): Promise<ResumeStatus> {
    const res = await apiClient.get<ResumeStatus>("/api/resume/status");
    return res.data;
  },

  async getProfile(resumeId?: string): Promise<CandidateProfile> {
    const url = resumeId ? `/api/resume/profile?resume_id=${resumeId}` : "/api/resume/profile";
    const res = await apiClient.get<CandidateProfile>(url);
    return res.data;
  },

  async getSummary(resumeId?: string): Promise<SummaryResponse> {
    const url = resumeId ? `/api/resume/summary?resume_id=${resumeId}` : "/api/resume/summary";
    const res = await apiClient.get<SummaryResponse>(url);
    return res.data;
  },

  async getLinks(resumeId?: string): Promise<LinksResponse> {
    const url = resumeId ? `/api/resume/links?resume_id=${resumeId}` : "/api/resume/links";
    const res = await apiClient.get<LinksResponse>(url);
    return res.data;
  },

  async uploadResume(file: File): Promise<UploadResumeResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await apiClient.post<UploadResumeResponse>("/api/resume/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      timeout: 90000,
    });
    return res.data;
  },

  async evaluateJD(jobDescription: string, resumeId?: string): Promise<JobFitEvaluation> {
    const res = await apiClient.post<JobFitEvaluation>("/api/evaluate-jd", {
      job_description: jobDescription,
      resume_id: resumeId,
    });
    return res.data;
  },

  async sendChatMessage(message: string, sessionId: string = "default", resumeId?: string): Promise<any> {
    const res = await apiClient.post("/api/chat", {
      message,
      session_id: sessionId,
      resume_id: resumeId,
    });
    return res.data;
  },

  async getHistory(sessionId: string = "default", resumeId?: string): Promise<any> {
    const url = resumeId
      ? `/api/chat/history?session_id=${sessionId}&resume_id=${resumeId}`
      : `/api/chat/history?session_id=${sessionId}`;
    const res = await apiClient.get(url);
    return res.data;
  },

  async clearHistory(sessionId: string = "default"): Promise<void> {
    await apiClient.delete(`/api/chat/history?session_id=${sessionId}`);
  },
};
