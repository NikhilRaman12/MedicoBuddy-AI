import { FileText, Bookmark } from "lucide-react";

import { Citation } from "../../api/schemas";

interface CitationCardProps {
  citation: Citation;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation }) => {
  const pageText = citation.page_number ? ` (Page ${citation.page_number})` : "";
  const scoreText = citation.retrieval_score ? `Score: ${(citation.retrieval_score * 100).toFixed(0)}%` : "";

  return (
    <div className="bg-navy-900 border border-navy-700 rounded-lg p-3 space-y-2 text-xs text-slate-300">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5 font-semibold text-teal-300">
          <FileText className="w-4 h-4 text-teal-400 shrink-0" />
          <span>
            [{citation.number}] {citation.title}
            {pageText}
          </span>
        </div>

        {scoreText && (
          <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-teal-950/80 border border-teal-800 text-teal-300">
            {scoreText}
          </span>
        )}
      </div>

      {citation.authors && (
        <div className="text-slate-400 text-[11px] flex items-center gap-1">
          <Bookmark className="w-3 h-3 text-slate-500" />
          <span>
            {citation.authors} {citation.publication_date && `(${citation.publication_date})`}
          </span>
        </div>
      )}

      {citation.source_file && (
        <div className="text-slate-400 text-[11px]">
          Source File: <span className="text-slate-300">{citation.source_file}</span>
        </div>
      )}

      {citation.supporting_passage && (
        <blockquote className="border-l-2 border-teal-500/60 pl-2 py-1 text-slate-300 italic bg-navy-800/40 rounded-r text-[11px]">
          "{citation.supporting_passage}"
        </blockquote>
      )}
    </div>
  );
};
