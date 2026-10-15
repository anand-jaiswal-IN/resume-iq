import React, { useState } from "react";
import { FileText, Trash2, CheckCircle2, Plus, Calendar, Layers } from "lucide-react";
import type { ResumeItem } from "../../lib/types";

interface ResumeListPanelProps {
  resumes: ResumeItem[];
  activeResumeId: string | null;
  onSelectResume: (resumeId: string) => void;
  onDeleteResume: (resumeId: string) => void;
  onOpenUpload: () => void;
  isLoading?: boolean;
}

export const ResumeListPanel: React.FC<ResumeListPanelProps> = ({
  resumes,
  activeResumeId,
  onSelectResume,
  onDeleteResume,
  onOpenUpload,
  isLoading = false,
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const formatFileSize = (bytes: number): string => {
    if (!bytes) return "0 KB";
    const kb = bytes / 1024;
    if (kb < 1024) return `${Math.round(kb)} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  };

  const formatDateTime = (isoString: string): string => {
    if (!isoString) return "";
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (deletingId === id) {
      onDeleteResume(id);
      setDeletingId(null);
    } else {
      setDeletingId(id);
      setTimeout(() => setDeletingId((curr) => (curr === id ? null : curr)), 4000);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-[#e6e5e0] p-4 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#e6e5e0]">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold tracking-tight text-[#26251e]">
            Indexed Resumes
          </h2>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#f7f7f4] border border-[#e6e5e0] text-[#5a5852]">
            {resumes.length}
          </span>
        </div>

        <button
          type="button"
          onClick={onOpenUpload}
          className="inline-flex items-center gap-1 text-xs font-medium text-[#f54e00] hover:text-[#d04200] transition-colors cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add</span>
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto pt-3 space-y-2 no-scrollbar min-h-[140px] max-h-[300px]">
        {isLoading && resumes.length === 0 ? (
          <div className="text-center py-6 text-xs text-[#807d72]">
            Loading resumes...
          </div>
        ) : resumes.length === 0 ? (
          <div className="text-center py-8 px-2 flex flex-col items-center">
            <div className="w-10 h-10 rounded-xl bg-[#f7f7f4] border border-[#e6e5e0] flex items-center justify-center p-1.5 mb-2 shadow-2xs">
              <img src="/favicon.ico" alt="Resume IQ" className="w-full h-full object-contain" />
            </div>
            <p className="text-xs text-[#5a5852] font-semibold">Welcome to Resume IQ</p>
            <p className="text-[11px] text-[#807d72] mt-0.5 max-w-[180px]">
              Upload a resume PDF to index into Qdrant and start asking questions.
            </p>
            <button
              type="button"
              onClick={onOpenUpload}
              className="mt-3 text-xs text-[#f54e00] font-medium hover:underline cursor-pointer"
            >
              + Upload first resume
            </button>
          </div>
        ) : (
          resumes.map((resume) => {
            const isActive = resume.id === activeResumeId;
            const isConfirming = deletingId === resume.id;

            return (
              <div
                key={resume.id}
                onClick={() => onSelectResume(resume.id)}
                className={`p-3 rounded-lg border transition-all cursor-pointer text-left relative group ${
                  isActive
                    ? "bg-[#fafaf7] border-[#f54e00]/60 ring-1 ring-[#f54e00]/20"
                    : "bg-white border-[#e6e5e0] hover:border-[#cfcdc4] hover:bg-[#f7f7f4]/50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold text-[#26251e] truncate">
                        {resume.candidate_name || resume.file_name}
                      </span>
                      {isActive && (
                        <span className="text-[10px] font-medium px-1.5 py-0.2 rounded bg-[#f54e00]/10 text-[#f54e00] flex-shrink-0">
                          Active
                        </span>
                      )}
                    </div>

                    {resume.headline && (
                      <p className="text-[11px] text-[#5a5852] truncate mt-0.5">
                        {resume.headline}
                      </p>
                    )}

                    {/* Metadata strip */}
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] text-[#807d72] mt-2 pt-2 border-t border-[#efeee8]">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-2.5 h-2.5 text-[#a09c92]" />
                        <span>{formatDateTime(resume.uploaded_at)}</span>
                      </span>

                      <span>•</span>

                      <span className="flex items-center gap-1 font-mono">
                        <span>{formatFileSize(resume.file_size)}</span>
                      </span>

                      {resume.total_chunks > 0 && (
                        <>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Layers className="w-2.5 h-2.5 text-[#a09c92]" />
                            <span>{resume.total_chunks} chunks</span>
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      type="button"
                      onClick={(e) => handleDeleteClick(e, resume.id)}
                      title={isConfirming ? "Click again to confirm delete" : "Delete resume"}
                      className={`p-1.5 rounded transition-colors cursor-pointer ${
                        isConfirming
                          ? "bg-[#cf2d56] text-white"
                          : "text-[#a09c92] hover:text-[#cf2d56] hover:bg-[#cf2d56]/10 opacity-70 group-hover:opacity-100"
                      }`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
