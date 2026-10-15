import React from "react";
import { Upload, LayoutDashboard, Briefcase, UserCheck } from "lucide-react";
import type { ResumeStatus } from "../../lib/types";

interface NavbarProps {
  resumeStatus: ResumeStatus | null;
  onOpenUpload: () => void;
  isBackendHealthy: boolean;
  activeTab: "chat" | "jd" | "profile";
  onSelectTab: (tab: "chat" | "jd" | "profile") => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenUpload,
  isBackendHealthy,
  activeTab,
  onSelectTab,
}) => {
  return (
    <header className="h-14 bg-[#f7f7f4] border-b border-[#e6e5e0] text-[#26251e] sticky top-0 z-50">
      <div className="max-w-[1280px] mx-auto w-full h-full px-4 sm:px-6 flex justify-between items-center">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div
            className="flex items-center gap-2.5 cursor-pointer select-none group"
            onClick={() => onSelectTab("chat")}
            title="Resume IQ — Go to Dashboard"
          >
            <img
              src="/favicon.ico"
              alt="Resume IQ Logo"
              className="w-8 h-8 rounded-lg object-contain transition-transform group-hover:scale-105"
            />
            <div className="flex items-center gap-1.5">
              <span className="text-base font-bold tracking-tight text-[#26251e]">
                Resume<span className="text-[#0284c7]">IQ</span>
              </span>
              <span className="hidden sm:inline-block text-[10px] font-semibold uppercase tracking-wider text-[#0284c7] bg-[#0284c7]/10 px-1.5 py-0.5 rounded-full">
                AI
              </span>
            </div>
          </div>

          <span className="text-[#cfcdc4] hidden sm:inline">/</span>

          {/* Minimal Live Status */}
          <div
            className="hidden sm:flex items-center gap-1.5 text-xs text-[#807d72]"
            title={isBackendHealthy ? "API connected" : "Connecting to backend..."}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isBackendHealthy ? "bg-[#1f8a65]" : "bg-[#c08532] animate-pulse"
              }`}
            />
            <span className="text-[11px] font-normal">
              {isBackendHealthy ? "Ready" : "Connecting"}
            </span>
          </div>
        </div>

        {/* Center Nav Views (like professional websites) */}
        <nav className="flex items-center gap-1 bg-[#efeee8] p-1 rounded-lg">
          <button
            type="button"
            onClick={() => onSelectTab("chat")}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
              activeTab === "chat"
                ? "bg-white text-[#26251e] shadow-none"
                : "text-[#5a5852] hover:text-[#26251e]"
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Dashboard & Chat</span>
          </button>

          <button
            type="button"
            onClick={() => onSelectTab("jd")}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
              activeTab === "jd"
                ? "bg-white text-[#26251e] shadow-none"
                : "text-[#5a5852] hover:text-[#26251e]"
            }`}
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>JD Matcher</span>
          </button>

          <button
            type="button"
            onClick={() => onSelectTab("profile")}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
              activeTab === "profile"
                ? "bg-white text-[#26251e] shadow-none"
                : "text-[#5a5852] hover:text-[#26251e]"
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Profile</span>
          </button>
        </nav>

        {/* Right CTA */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onOpenUpload}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#f54e00] hover:bg-[#d04200] text-white text-xs font-medium rounded-lg transition-colors cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Resume</span>
          </button>
        </div>
      </div>
    </header>
  );
};
