import React, { useState } from "react";
import { MessageSquare, Plus, Trash2, Clock } from "lucide-react";
import type { ChatSessionSummary } from "../../lib/types";

interface SessionListPanelProps {
  sessions: ChatSessionSummary[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  isLoading?: boolean;
}

export const SessionListPanel: React.FC<SessionListPanelProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  isLoading = false,
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const formatTime = (isoString: string): string => {
    if (!isoString) return "";
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (deletingId === id) {
      onDeleteSession(id);
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
            Chat Sessions
          </h2>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#f7f7f4] border border-[#e6e5e0] text-[#5a5852]">
            {sessions.length}
          </span>
        </div>

        <button
          type="button"
          onClick={onCreateSession}
          className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#26251e] hover:bg-black text-[#f7f7f4] text-xs font-medium rounded-md transition-colors cursor-pointer"
        >
          <Plus className="w-3 h-3" />
          <span>New Chat</span>
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto pt-3 space-y-1.5 no-scrollbar min-h-[140px] max-h-[300px]">
        {isLoading && sessions.length === 0 ? (
          <div className="text-center py-6 text-xs text-[#807d72]">
            Loading sessions...
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-6 px-2 text-xs text-[#807d72]">
            <p>No active sessions.</p>
            <button
              type="button"
              onClick={onCreateSession}
              className="mt-2 text-xs text-[#f54e00] hover:underline cursor-pointer"
            >
              + Create new chat
            </button>
          </div>
        ) : (
          sessions.map((sess) => {
            const isActive = sess.id === activeSessionId;
            const isConfirming = deletingId === sess.id;

            return (
              <div
                key={sess.id}
                onClick={() => onSelectSession(sess.id)}
                className={`p-2.5 rounded-lg border transition-all cursor-pointer text-left flex items-center justify-between gap-2 group ${
                  isActive
                    ? "bg-[#fafaf7] border-[#26251e] text-[#26251e] font-medium"
                    : "bg-white border-[#e6e5e0] text-[#5a5852] hover:border-[#cfcdc4] hover:bg-[#f7f7f4]/50"
                }`}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <MessageSquare
                    className={`w-3.5 h-3.5 flex-shrink-0 ${
                      isActive ? "text-[#f54e00]" : "text-[#a09c92]"
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs truncate">{sess.title}</p>
                    <div className="flex items-center gap-2 text-[10px] text-[#807d72] mt-0.5">
                      {sess.message_count > 0 && (
                        <span>{sess.message_count} msgs</span>
                      )}
                      {sess.updated_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-2.5 h-2.5 text-[#a09c92]" />
                          <span>{formatTime(sess.updated_at)}</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Delete session button */}
                <button
                  type="button"
                  onClick={(e) => handleDelete(e, sess.id)}
                  title={isConfirming ? "Confirm delete" : "Delete session"}
                  className={`p-1 rounded text-xs transition-colors cursor-pointer ${
                    isConfirming
                      ? "bg-[#cf2d56] text-white"
                      : "text-[#a09c92] hover:text-[#cf2d56] hover:bg-[#cf2d56]/10 opacity-70 group-hover:opacity-100"
                  }`}
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
