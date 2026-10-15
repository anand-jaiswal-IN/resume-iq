import React, { useState } from "react";
import {
  Briefcase,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Award,
  HelpCircle,
  FileCheck,
  Loader2,
} from "lucide-react";
import { api } from "../../lib/api";
import { jdInputSchema } from "../../lib/validations";
import type { JobFitEvaluation } from "../../lib/types";

const SAMPLE_FULLSTACK_AI_JD = `Role: Full Stack AI Engineer (Junior / Mid-Level)
Location: Remote / Hybrid
About the Job:
We are looking for a Full Stack AI Engineer to design and deploy modern web applications integrating generative AI, LangChain, and real-time data flows.

Key Requirements:
- Strong proficiency in Python, JavaScript/TypeScript, and React or Next.js
- Hands-on experience building RAG systems with LangChain, Vector Databases (ChromaDB, Pinecone, or FAISS)
- Experience designing RESTful APIs using FastAPI, Node.js, or Django
- Familiarity with containerization using Docker
- Knowledge of relational databases (PostgreSQL/MySQL) and Redis caching
- Real-time communication using WebSockets / Socket.io is a huge plus
- Nice-to-have: Cloud deployment experience with AWS EC2 or modern hosting platforms`;

interface JDEvaluatorViewProps {
  activeResumeId?: string | null;
  activeResumeName?: string | null;
}

export const JDEvaluatorView: React.FC<JDEvaluatorViewProps> = ({
  activeResumeId,
  activeResumeName,
}) => {
  const [jdText, setJdText] = useState("");
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluation, setEvaluation] = useState<JobFitEvaluation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    setError(null);
    const result = jdInputSchema.safeParse(jdText);
    if (!result.success) {
      setError(result.error.issues[0]?.message || "Invalid Job Description");
      return;
    }

    setIsEvaluating(true);
    try {
      const res = await api.evaluateJD(result.data, activeResumeId || undefined);
      setEvaluation(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || "Failed to evaluate job description.");
    } finally {
      setIsEvaluating(false);
    }
  };

  const loadSample = () => {
    setJdText(SAMPLE_FULLSTACK_AI_JD);
    setError(null);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-[#1f8a65]";
    if (score >= 65) return "text-[#c08532]";
    if (score >= 50) return "text-[#f54e00]";
    return "text-[#cf2d56]";
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Column: JD Input (5 cols) */}
      <div className="lg:col-span-5 flex flex-col gap-4">
        <div className="bg-white border border-[#e6e5e0] rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#e6e5e0] text-[#26251e] flex items-center justify-center">
                <Briefcase className="w-4 h-4" />
              </div>
              <h2 className="text-lg font-normal tracking-tight text-[#26251e]">
                Job Description
              </h2>
            </div>
            <button
              type="button"
              onClick={loadSample}
              className="text-xs text-[#f54e00] hover:underline cursor-pointer"
            >
              Load Sample JD
            </button>
          </div>

          <p className="text-xs text-[#807d72] mb-3">
            Paste any role description or job requirements to calculate an instant 0–100% fit score, matched strengths, skill gaps, and interview questions.
          </p>

          <textarea
            value={jdText}
            onChange={(e) => {
              setJdText(e.target.value);
              if (error) setError(null);
            }}
            placeholder="Paste Job Description here (e.g. requirements, tech stack, responsibilities)..."
            rows={14}
            className="w-full bg-[#fafaf7] border border-[#e6e5e0] rounded-xl p-4 text-sm text-[#26251e] font-mono focus:border-[#f54e00] focus:ring-1 focus:ring-[#f54e00]/20 placeholder-[#a09c92] outline-none transition-colors resize-y"
          />

          <div className="flex justify-between items-center mt-2 text-xs text-[#a09c92] px-1">
            <span>{jdText.length} characters</span>
            {jdText ? (
              <button
                type="button"
                onClick={() => setJdText("")}
                className="text-[#a09c92] hover:text-[#26251e] transition-colors cursor-pointer"
              >
                Clear
              </button>
            ) : null}
          </div>

          {error && (
            <div className="mt-3 bg-[#cf2d56]/10 border border-[#cf2d56]/20 text-[#cf2d56] rounded-lg p-3 text-xs">
              {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleEvaluate}
            disabled={isEvaluating || !jdText.trim()}
            className="mt-4 bg-[#f54e00] hover:bg-[#d04200] text-white rounded-lg py-3 w-full text-sm font-medium disabled:opacity-40 flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed transition-colors"
          >
            {isEvaluating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Analyzing Profile & Scoring...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-white" />
                <span>Evaluate Candidate Fit</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Right Column: Results Scorecard (7 cols) */}
      <div className="lg:col-span-7">
        {evaluation ? (
          <div className="flex flex-col gap-5">
            {/* Score Banner Card */}
            <div className="bg-white border border-[#e6e5e0] rounded-xl p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] uppercase tracking-[0.88px] font-semibold text-[#807d72] mb-1">
                    Recruiter Scorecard
                  </div>
                  <h3 className="text-xl font-normal tracking-tight text-[#26251e]">
                    {evaluation.target_role}
                  </h3>
                  <div className="text-xs text-[#f54e00] font-medium mt-0.5">
                    Evaluated candidate: {evaluation.candidate_name}
                  </div>
                </div>

                {/* Score Pill */}
                <div className="bg-[#f7f7f4] border border-[#e6e5e0] rounded-xl px-5 py-3 flex items-center gap-3">
                  <div className="text-3xl font-normal text-[#26251e]">
                    {evaluation.fit_score}%
                  </div>
                  <div className="text-left">
                    <div className="text-xs text-[#5a5852]">Verdict</div>
                    <div className={`text-xs font-semibold ${getScoreColor(evaluation.fit_score)}`}>
                      {evaluation.verdict}
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommendation quote */}
              <div className="mt-4 bg-[#fafaf7] border border-[#efeee8] rounded-lg p-4 text-sm text-[#5a5852] italic">
                "{evaluation.recommendation_summary}"
              </div>
            </div>

            {/* Matched Skills / Missing Gaps (2-column grid) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Matched Skills */}
              <div className="bg-white border border-[#e6e5e0] rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-[#1f8a65]">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Matched Skills & Strengths</span>
                </div>
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {evaluation.matched_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="bg-[#1f8a65]/10 text-[#1f8a65] rounded-full text-xs px-2.5 py-1 font-medium"
                    >
                      ✓ {skill}
                    </span>
                  ))}
                </div>
                <div className="space-y-1.5 pt-2 border-t border-[#efeee8]">
                  {evaluation.strengths.map((str, i) => (
                    <div key={i} className="text-xs text-[#5a5852] flex items-start gap-1.5">
                      <span className="text-[#1f8a65] font-semibold">•</span>
                      <span>{str}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Missing Gaps */}
              <div className="bg-white border border-[#e6e5e0] rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-[#cf2d56]">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Identified Gaps & Missing Skills</span>
                </div>
                {evaluation.missing_skills_or_gaps.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {evaluation.missing_skills_or_gaps.map((gap, i) => (
                      <span
                        key={i}
                        className="bg-[#cf2d56]/10 text-[#cf2d56] rounded-full text-xs px-2.5 py-1 font-medium"
                      >
                        ▲ {gap}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-[#1f8a65] font-medium mb-3">
                    No critical skill gaps identified!
                  </div>
                )}
                <div className="text-xs text-[#a09c92] mt-2">
                  * Gaps can be verified during the interview or bridged with quick on-the-job training.
                </div>
              </div>
            </div>

            {/* Relevant Projects */}
            {evaluation.relevant_projects.length > 0 && (
              <div className="bg-white border border-[#e6e5e0] rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-[#26251e]">
                  <FileCheck className="w-4 h-4 text-[#807d72]" />
                  <span>Projects Providing Direct Proof</span>
                </div>
                <div className="space-y-2">
                  {evaluation.relevant_projects.map((proj, i) => (
                    <div
                      key={i}
                      className="bg-[#fafaf7] border border-[#efeee8] rounded-lg p-3 text-xs text-[#26251e]"
                    >
                      {proj}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Interview Questions */}
            {evaluation.suggested_interview_questions.length > 0 && (
              <div className="bg-white border border-[#e6e5e0] rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-[#26251e]">
                  <HelpCircle className="w-4 h-4 text-[#807d72]" />
                  <span>Suggested Technical Interview Questions</span>
                </div>
                <div className="space-y-2">
                  {evaluation.suggested_interview_questions.map((q, i) => (
                    <div
                      key={i}
                      className="bg-[#fafaf7] border border-[#efeee8] rounded-lg p-3 text-xs text-[#26251e]"
                    >
                      <span className="text-[#f54e00] font-semibold mr-1.5">Q{i + 1}:</span>
                      <span>{q}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Empty state (no evaluation) */
          <div className="h-full min-h-[450px] bg-white border border-[#e6e5e0] rounded-xl p-8 flex flex-col items-center justify-center text-center">
            <div className="bg-[#e6e5e0] rounded-xl p-4 text-[#26251e] mb-4">
              <Award className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-normal tracking-tight text-[#26251e] mb-1">
              Ready for Job Matching
            </h3>
            <p className="text-xs text-[#807d72] max-w-md mb-4">
              Paste a Job Description on the left and click Evaluate Candidate Fit to generate an AI-powered recruiter scorecard with quantitative match scoring.
            </p>
            <button
              type="button"
              onClick={loadSample}
              className="bg-white border border-[#cfcdc4] hover:border-[#807d72] text-[#26251e] rounded-lg text-xs px-3.5 py-2 font-medium transition-colors cursor-pointer"
            >
              Try with Sample JD
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
