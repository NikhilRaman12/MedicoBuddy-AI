import React from "react";
import { X, Search, FileCheck, Info } from "lucide-react";
import { MedicoBuddyResponse } from "../../api/schemas";
import { CitationCard } from "./CitationCard";
import { GraphPath } from "./GraphPath";

interface EvidenceDrawerProps {
  data: MedicoBuddyResponse | null;
  requestId?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  data,
  requestId = "",
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  const citations = data?.citations || [];
  const evidenceLevel = data?.overall_evidence_level || "MODERATE";

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-md bg-navy-800 border-l border-navy-700 shadow-2xl z-50 flex flex-col transition-all">
      {/* Drawer Header */}
      <div className="p-4 border-b border-navy-700 flex items-center justify-between bg-navy-900/60">
        <div className="flex items-center gap-2">
          <Search className="w-5 h-5 text-teal-400" />
          <h3 className="font-semibold text-slate-100 text-sm">
            Grounded Evidence Drawer
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-navy-700 rounded-lg text-slate-400 hover:text-slate-200"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Drawer Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {data ? (
          <>
            {/* Overview Summary Box */}
            <div className="bg-navy-900 p-3.5 rounded-xl border border-navy-700 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Overall Evidence Level:</span>
                <span className="font-semibold px-2 py-0.5 rounded bg-teal-950/80 border border-teal-800 text-teal-300">
                  {evidenceLevel}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Retrieved Sources Count:</span>
                <span className="font-semibold text-slate-200">{citations.length}</span>
              </div>
              {requestId && (
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Request ID:</span>
                  <span className="font-mono text-slate-300 truncate max-w-[180px]">
                    {requestId}
                  </span>
                </div>
              )}
            </div>

            {/* Validated Citations */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <FileCheck className="w-3.5 h-3.5 text-teal-400" />
                Validated Source Citations ({citations.length})
              </h4>

              {citations.length > 0 ? (
                <div className="space-y-3">
                  {citations.map((c, idx) => (
                    <CitationCard key={idx} citation={c} />
                  ))}
                </div>
              ) : (
                <div className="bg-navy-900/60 p-3 rounded-lg border border-navy-700 text-xs text-slate-400 flex items-center gap-2">
                  <Info className="w-4 h-4 text-slate-500 shrink-0" />
                  <span>No validated source evidence was retrieved for this response.</span>
                </div>
              )}
            </div>

            {/* Neo4j Graph Path */}
            <GraphPath graphContext={data.retrieval_diagnostics?.graph_context || []} />
          </>
        ) : (
          <div className="text-center py-12 text-slate-400 text-sm">
            Select a response to inspect evidence provenance.
          </div>
        )}
      </div>
    </div>
  );
};
