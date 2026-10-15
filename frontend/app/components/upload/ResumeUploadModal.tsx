import React, { useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  LinearProgress,
} from "@mui/material";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, X } from "lucide-react";
import { validateResumeFile } from "../../lib/validations";
import { api } from "../../lib/api";

interface ResumeUploadModalProps {
  open: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

export const ResumeUploadModal: React.FC<ResumeUploadModalProps> = ({
  open,
  onClose,
  onUploadSuccess,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileSelect = (file: File) => {
    setError(null);
    const validation = validateResumeFile(file);
    if (!validation.valid) {
      setError(validation.error || "Invalid file");
      return;
    }
    setSelectedFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);
    setUploadStep("1/3 Uploading & extracting text/links...");

    try {
      setTimeout(() => setUploadStep("2/3 Semantic chunking & indexing into ChromaDB..."), 2500);
      setTimeout(() => setUploadStep("3/3 Extracting structured candidate profile with Gemini..."), 6000);

      await api.uploadResume(selectedFile);
      setUploadStep("Complete!");
      setTimeout(() => {
        setIsUploading(false);
        setSelectedFile(null);
        onUploadSuccess();
        onClose();
      }, 800);
    } catch (err: any) {
      setIsUploading(false);
      setError(err?.response?.data?.detail || err.message || "Failed to upload and parse resume.");
    }
  };

  const handleModalClose = () => {
    if (!isUploading) {
      setSelectedFile(null);
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleModalClose}
      maxWidth="sm"
      fullWidth
      {...({
        PaperProps: {
          elevation: 0,
          sx: {
            borderRadius: "12px",
            backgroundImage: "none",
            backgroundColor: "#ffffff",
            border: "1px solid #e6e5e0",
            boxShadow: "none",
          },
        },
      } as any)}
      slotProps={{
        paper: {
          elevation: 0,
          sx: {
            borderRadius: "12px",
            backgroundImage: "none",
            backgroundColor: "#ffffff",
            border: "1px solid #e6e5e0",
            boxShadow: "none",
          },
        },
      }}
    >
      <div className="flex justify-between items-center px-6 pt-6 pb-2">
        <div className="flex items-center gap-3">
          <img
            src="/logo.png"
            alt="Resume IQ"
            className="h-9 w-auto object-contain"
          />
          <div>
            <h2 className="text-base font-semibold tracking-tight text-[#26251e]">
              Upload Resume
            </h2>
            <p className="text-[11px] text-[#807d72]">
              Index into ChromaDB for interactive AI Q&A
            </p>
          </div>
        </div>
        {!isUploading && (
          <button
            onClick={handleModalClose}
            className="text-[#807d72] hover:text-[#26251e] p-1.5 rounded-lg hover:bg-[#fafaf7] transition-colors cursor-pointer"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <DialogContent sx={{ padding: "16px 24px 0" }}>
        <p className="text-xs text-[#5a5852] mb-4 leading-relaxed">
          Upload a 1–2 page resume PDF. Resume IQ extracts semantic sections, links, and builds an MMR vector store with Gemini.
        </p>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-[#cf2d56]/10 border border-[#cf2d56]/20 text-[#cf2d56] text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Drop Zone */}
        <input
          type="file"
          ref={fileInputRef}
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors duration-150 flex flex-col items-center justify-center ${
            isDragging
              ? "border-[#f54e00] bg-[#f54e00]/5"
              : "border-[#cfcdc4] bg-[#fafaf7] hover:border-[#807d72]"
          } ${isUploading ? "pointer-events-none opacity-60" : ""}`}
        >
          {selectedFile ? (
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-lg bg-[#f54e00]/10 text-[#f54e00] flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <div className="font-semibold text-sm text-[#26251e]">
                {selectedFile.name}
              </div>
              <div className="text-xs text-[#807d72]">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready to ingest
              </div>
              <span className="text-xs text-[#f54e00] hover:underline mt-1 font-medium">
                Click to choose a different file
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div className="w-12 h-12 rounded-xl bg-white border border-[#e6e5e0] flex items-center justify-center p-2 shadow-2xs">
                <img src="/favicon.ico" alt="Resume IQ" className="w-full h-full object-contain" />
              </div>
              <div className="text-sm text-[#5a5852]">
                Drag & drop your resume PDF here, or <span className="text-[#f54e00] font-medium">browse</span>
              </div>
              <div className="text-[11px] text-[#a09c92]">
                Maximum file size: 15MB (.pdf only)
              </div>
            </div>
          )}
        </div>

        {/* Upload Progress Status */}
        {isUploading && (
          <div className="mt-4 p-4 rounded-lg bg-[#fafaf7] border border-[#efeee8]">
            <div className="flex justify-between items-center text-xs font-medium mb-2.5 text-[#f54e00]">
              <span>{uploadStep}</span>
              <span className="animate-pulse text-[#807d72]">Processing...</span>
            </div>
            <LinearProgress
              sx={{
                borderRadius: "9999px",
                height: 6,
                backgroundColor: "rgba(245, 78, 0, 0.12)",
                "& .MuiLinearProgress-bar": {
                  backgroundColor: "#f54e00",
                },
              }}
            />
          </div>
        )}
      </DialogContent>

      <div className="px-6 pb-6 pt-5 flex justify-end gap-2.5">
        <button
          type="button"
          onClick={handleModalClose}
          disabled={isUploading}
          className="px-4 py-2 rounded-lg bg-white border border-[#cfcdc4] text-xs font-medium text-[#26251e] hover:bg-[#fafaf7] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          className="px-4 py-2 rounded-lg bg-[#f54e00] text-xs font-medium text-white hover:bg-[#d04200] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>{isUploading ? "Ingesting..." : "Upload & Analyze"}</span>
        </button>
      </div>
    </Dialog>
  );
};
