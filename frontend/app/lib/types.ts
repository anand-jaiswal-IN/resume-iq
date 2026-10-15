/**
 * TypeScript Data Models matching FastAPI Backend Schemas.
 */

export interface CategorizedSkills {
  languages: string[];
  frontend: string[];
  backend: string[];
  databases: string[];
  cloud_and_devops: string[];
  ai_and_ml: string[];
  tools: string[];
}

export interface WorkExperienceItem {
  company: string;
  role: string;
  duration: string;
  responsibilities: string[];
}

export interface ProjectItem {
  title: string;
  technologies: string[];
  description: string;
  link?: string | null;
}

export interface EducationItem {
  institution: string;
  degree: string;
  duration: string;
  score?: string | null;
}

export interface CandidateProfile {
  full_name: string;
  headline_or_role: string;
  summary?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  location?: string | null;
  links: string[];
  skills: CategorizedSkills;
  work_experience: WorkExperienceItem[];
  projects: ProjectItem[];
  education: EducationItem[];
  certifications: string[];
}

export interface JobFitEvaluation {
  candidate_name: string;
  target_role: string;
  fit_score: number;
  verdict: "Strong Match" | "Good Match" | "Moderate Fit" | "Low Fit / Significant Upskilling Needed";
  strengths: string[];
  matched_skills: string[];
  missing_skills_or_gaps: string[];
  relevant_projects: string[];
  recommendation_summary: string;
  suggested_interview_questions: string[];
}

export interface ResumeStatus {
  is_loaded: boolean;
  file_name: string | null;
  candidate_name: string | null;
  headline: string | null;
  total_chunks: number;
  total_links: number;
  active_resume_id?: string | null;
  total_resumes?: number;
}

export interface ResumeItem {
  id: string;
  file_name: string;
  file_size: number;
  uploaded_at: string;
  candidate_name: string | null;
  headline: string | null;
  total_pages: number;
  total_chunks: number;
  links_count: number;
  is_active: boolean;
}

export interface ResumeListResponse {
  resumes: ResumeItem[];
  active_resume_id: string | null;
  total: number;
}

export interface UploadResumeResponse {
  success: boolean;
  message: string;
  id: string;
  file_name: string;
  file_size: number;
  uploaded_at: string;
  total_pages: number;
  total_chunks: number;
  links_count: number;
  candidate_name: string;
  headline: string;
  is_active: boolean;
}

export interface LinksResponse {
  file_name: string | null;
  total_links: number;
  links: string[];
}

export interface SummaryResponse {
  candidate_name: string;
  summary: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  message: string;
}

export interface StatsResponse {
  collection_name: string;
  document_count: number;
  has_profile: boolean;
  candidate_name: string | null;
}

export interface ChatSessionSummary {
  id: string;
  resume_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string | null;
}

export type IntentType = "FACTUAL_QA" | "GENERAL_CONVERSATION" | "JD_EVALUATION" | "RESUME_SUMMARY";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: IntentType;
  timestamp: string;
  jd_result?: JobFitEvaluation;
  isStreaming?: boolean;
}

export interface ChatSessionDetail {
  id: string;
  resume_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}
