import React, { useEffect, useState } from "react";
import {
  Mail,
  Phone,
  MapPin,
  ExternalLink,
  Code2,
  Briefcase,
  Layers,
  GraduationCap,
  Link as LinkIcon,
  Sparkles,
} from "lucide-react";
import { api } from "../../lib/api";
import type { CandidateProfile, LinksResponse } from "../../lib/types";

interface CandidateProfileViewProps {
  activeResumeId?: string | null;
}

export const CandidateProfileView: React.FC<CandidateProfileViewProps> = ({ activeResumeId }) => {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [linksData, setLinksData] = useState<LinksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [profRes, linksRes] = await Promise.all([
          api.getProfile(activeResumeId || undefined),
          api.getLinks(activeResumeId || undefined),
        ]);
        setProfile(profRes);
        setLinksData(linksRes);
      } catch (err: any) {
        setError(err?.response?.data?.detail || "No candidate profile found. Please upload a resume.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [activeResumeId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 min-h-[400px]">
        <svg
          className="animate-spin h-6 w-6 text-[#807d72]"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="3"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <p className="mt-3 text-xs text-[#807d72]">
          Loading candidate profile...
        </p>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="p-8 text-center rounded-xl bg-white border border-[#e6e5e0]">
        <p className="text-sm text-[#5a5852] mb-1">
          {error || "No candidate profile available."}
        </p>
        <p className="text-xs text-[#807d72]">
          Upload a resume PDF to view the structured candidate profile.
        </p>
      </div>
    );
  }

  const s = profile.skills;

  return (
    <div className="space-y-6">
      {/* Identity Header */}
      <div className="p-8 rounded-xl bg-white border border-[#e6e5e0]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#f54e00] text-white flex items-center justify-center text-xl font-medium shrink-0">
              {profile.full_name ? profile.full_name.charAt(0) : "U"}
            </div>
            <div>
              <h1 className="text-2xl font-normal tracking-tight text-[#26251e]">
                {profile.full_name}
              </h1>
              <div className="text-sm text-[#5a5852] mt-0.5">
                {profile.headline_or_role}
              </div>
              <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-[#807d72]">
                {profile.contact_email && (
                  <a
                    href={`mailto:${profile.contact_email}`}
                    className="flex items-center gap-1.5 hover:text-[#f54e00] transition-colors"
                  >
                    <Mail className="w-3.5 h-3.5" />
                    <span>{profile.contact_email}</span>
                  </a>
                )}
                {profile.contact_phone && (
                  <span className="flex items-center gap-1.5">
                    <Phone className="w-3.5 h-3.5" />
                    <span>{profile.contact_phone}</span>
                  </span>
                )}
                {profile.location && (
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>{profile.location}</span>
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Social / Portfolio Quick Links */}
          {profile.links && profile.links.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {profile.links.map((link, idx) => {
                let label = "Link";
                if (link.includes("linkedin.com")) label = "LinkedIn";
                else if (link.includes("github.com")) label = "GitHub";
                else if (link.includes("vercel.app") || link.includes("portfolio")) label = "Portfolio";
                else if (link.includes("codolio")) label = "Codolio";

                return (
                  <a
                    key={idx}
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-[#5a5852] bg-[#fafaf7] border border-[#e6e5e0] hover:border-[#f54e00] hover:text-[#f54e00] transition-colors"
                  >
                    <ExternalLink className="w-3 h-3 text-[#807d72]" />
                    <span>{label}</span>
                  </a>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Grid: 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Technical Skills Card (7 Cols) */}
        <div className="lg:col-span-7 p-6 rounded-xl bg-white border border-[#e6e5e0] flex flex-col gap-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#e6e5e0] text-[#26251e] flex items-center justify-center shrink-0">
              <Code2 className="w-4 h-4" />
            </div>
            <h2 className="text-base font-normal tracking-tight text-[#26251e]">
              Technical Competencies
            </h2>
          </div>

          <div className="space-y-4">
            {s.ai_and_ml && s.ai_and_ml.length > 0 && (
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72] mb-2 flex items-center gap-1.5">
                  <Sparkles className="w-3 h-3" />
                  <span>AI & GenAI</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {s.ai_and_ml.map((item, i) => (
                    <span
                      key={i}
                      className="bg-[#e6e5e0] text-[#26251e] rounded-full text-xs px-2.5 py-0.5"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {s.languages && s.languages.length > 0 && (
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72] mb-2">
                  Programming Languages
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {s.languages.map((item, i) => (
                    <span
                      key={i}
                      className="bg-[#e6e5e0] text-[#26251e] rounded-full text-xs px-2.5 py-0.5"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {s.frontend && s.frontend.length > 0 && (
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72] mb-2">
                  Frontend & UI
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {s.frontend.map((item, i) => (
                    <span
                      key={i}
                      className="bg-[#e6e5e0] text-[#26251e] rounded-full text-xs px-2.5 py-0.5"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {s.backend && s.backend.length > 0 && (
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72] mb-2">
                  Backend & APIs
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {s.backend.map((item, i) => (
                    <span
                      key={i}
                      className="bg-[#e6e5e0] text-[#26251e] rounded-full text-xs px-2.5 py-0.5"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {s.databases && s.databases.length > 0 && (
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72] mb-2">
                  Databases & Caches
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {s.databases.map((item, i) => (
                    <span
                      key={i}
                      className="bg-[#e6e5e0] text-[#26251e] rounded-full text-xs px-2.5 py-0.5"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {s.cloud_and_devops && s.cloud_and_devops.length > 0 && (
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72] mb-2">
                  DevOps & Cloud
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {s.cloud_and_devops.map((item, i) => (
                    <span
                      key={i}
                      className="bg-[#e6e5e0] text-[#26251e] rounded-full text-xs px-2.5 py-0.5"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {s.tools && s.tools.length > 0 && (
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.88px] text-[#807d72] mb-2">
                  Developer Tools
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {s.tools.map((item, i) => (
                    <span
                      key={i}
                      className="bg-[#e6e5e0] text-[#26251e] rounded-full text-xs px-2.5 py-0.5"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Work Experience Card (5 Cols) */}
        <div className="lg:col-span-5 p-6 rounded-xl bg-white border border-[#e6e5e0] flex flex-col gap-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#e6e5e0] text-[#26251e] flex items-center justify-center shrink-0">
              <Briefcase className="w-4 h-4" />
            </div>
            <h2 className="text-base font-normal tracking-tight text-[#26251e]">
              Work Experience
            </h2>
          </div>

          <div className="space-y-3">
            {profile.work_experience.map((exp, idx) => (
              <div
                key={idx}
                className="bg-[#fafaf7] border border-[#efeee8] rounded-lg p-4"
              >
                <div className="text-sm font-semibold text-[#26251e]">
                  {exp.company}
                </div>
                <div className="text-xs text-[#f54e00] mt-0.5">
                  {exp.role}
                </div>
                <div className="text-[11px] text-[#a09c92] mb-2">
                  {exp.duration}
                </div>
                <ul className="space-y-1 text-xs text-[#5a5852] list-disc pl-4">
                  {exp.responsibilities.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Education Box */}
          {profile.education && profile.education.length > 0 && (
            <div className="mt-2 pt-4 border-t border-[#e6e5e0]">
              <div className="text-[11px] uppercase tracking-[0.88px] text-[#807d72] mb-3 flex items-center gap-1.5">
                <GraduationCap className="w-3.5 h-3.5" />
                <span>Education</span>
              </div>
              <div className="space-y-3">
                {profile.education.map((edu, idx) => (
                  <div key={idx} className="space-y-0.5">
                    <div className="text-sm font-semibold text-[#26251e]">{edu.institution}</div>
                    <div className="text-xs text-[#5a5852]">{edu.degree}</div>
                    <div className="flex items-center justify-between text-[11px] text-[#a09c92] pt-0.5">
                      <span>{edu.duration}</span>
                      {edu.score && <span className="text-[#1f8a65] font-semibold">CGPA: {edu.score}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Key Projects Card (12 Cols) */}
        {profile.projects && profile.projects.length > 0 && (
          <div className="lg:col-span-12 p-6 rounded-xl bg-white border border-[#e6e5e0]">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-[#e6e5e0] text-[#26251e] flex items-center justify-center shrink-0">
                <Layers className="w-4 h-4" />
              </div>
              <h2 className="text-base font-normal tracking-tight text-[#26251e]">
                Featured Projects
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {profile.projects.map((proj, idx) => (
                <div
                  key={idx}
                  className="bg-[#fafaf7] border border-[#efeee8] rounded-lg p-5 flex flex-col justify-between group transition-colors hover:border-[#cfcdc4]"
                >
                  <div>
                    <div className="mb-2">
                      {proj.link ? (
                        <a
                          href={proj.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-semibold text-[#26251e] hover:text-[#f54e00] transition-colors inline-flex items-center gap-1.5"
                        >
                          <span>{proj.title}</span>
                          <ExternalLink className="w-3 h-3 text-[#807d72]" />
                        </a>
                      ) : (
                        <div className="text-sm font-semibold text-[#26251e] hover:text-[#f54e00] transition-colors">
                          {proj.title}
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-[#5a5852] mb-3 leading-relaxed">
                      {proj.description}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-1 pt-3 border-t border-[#efeee8]">
                    {proj.technologies.map((t, i) => (
                      <span
                        key={i}
                        className="bg-[#e6e5e0] text-[#26251e] rounded text-[10px] px-2 py-0.5"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Extracted Hyperlinks Explorer (12 Cols) */}
        {linksData && linksData.links && linksData.links.length > 0 && (
          <div className="lg:col-span-12 p-6 rounded-xl bg-white border border-[#e6e5e0]">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-[#e6e5e0] text-[#26251e] flex items-center justify-center shrink-0">
                <LinkIcon className="w-4 h-4" />
              </div>
              <h2 className="text-base font-normal tracking-tight text-[#26251e]">
                Extracted Resume Hyperlinks ({linksData.total_links})
              </h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
              {linksData.links.map((url, i) => (
                <a
                  key={i}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between p-2.5 rounded-lg bg-[#fafaf7] border border-[#efeee8] text-xs text-[#5a5852] hover:text-[#f54e00] hover:border-[#f54e00] transition-colors overflow-hidden group"
                >
                  <span className="truncate mr-2 font-mono text-[11px]">{url}</span>
                  <ExternalLink className="w-3.5 h-3.5 shrink-0 text-[#807d72] group-hover:text-[#f54e00] transition-colors" />
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
