import React from "react";
import { GitCommit } from "lucide-react";

interface GraphPathProps {
  graphContext?: any[];
}

export const GraphPath: React.FC<GraphPathProps> = ({ graphContext = [] }) => {
  const paths: string[] = [];

  if (Array.isArray(graphContext)) {
    graphContext.forEach((g) => {
      if (g && typeof g === "object" && g.relationship) {
        paths.push(
          `(${g.symptom || "Symptom"}) -[:${g.relationship}]-> (${g.action || "Action"})`
        );
      }
    });
  }

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
        <GitCommit className="w-3.5 h-3.5 text-teal-400" />
        Neo4j Knowledge Graph Traversal Path
      </h4>

      {paths.length > 0 ? (
        <div className="space-y-1.5">
          {paths.map((p, idx) => (
            <div
              key={idx}
              className="bg-navy-900 border border-navy-700 font-mono text-[11px] p-2 rounded text-teal-300 overflow-x-auto"
            >
              {p}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-slate-400 italic bg-navy-900/60 p-2 rounded border border-navy-700/60">
          No graph relationship available for this response.
        </p>
      )}
    </div>
  );
};
