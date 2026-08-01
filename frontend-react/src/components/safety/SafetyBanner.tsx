import React from "react";
import { AlertTriangle, ShieldCheck, AlertOctagon } from "lucide-react";

interface SafetyBannerProps {
  safetyStatus: string;
  triageOutcome?: string;
}

export const SafetyBanner: React.FC<SafetyBannerProps> = ({
  safetyStatus,
  triageOutcome = "",
}) => {
  const statusLower = safetyStatus.toLowerCase();
  const triageLower = triageOutcome.toLowerCase();

  const isUrgent =
    statusLower.includes("urgent") ||
    statusLower.includes("emergency") ||
    triageLower === "urgent_care" ||
    triageLower === "emergency";

  const isWarning = statusLower.includes("warning") || statusLower.includes("professional");

  if (isUrgent) {
    return (
      <div className="bg-red-950/40 border-l-4 border-red-500 text-red-200 p-4 rounded-r-lg mb-4 flex items-start gap-3 shadow-sm">
        <AlertOctagon className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold text-red-300">⚠️ Urgent Care Recommended</h4>
          <p className="text-sm text-red-200/90 mt-1">{safetyStatus}</p>
        </div>
      </div>
    );
  }

  if (isWarning) {
    return (
      <div className="bg-amber-950/40 border-l-4 border-amber-500 text-amber-200 p-4 rounded-r-lg mb-4 flex items-start gap-3 shadow-sm">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold text-amber-300">⚠️ Professional Evaluation Advised</h4>
          <p className="text-sm text-amber-200/90 mt-1">{safetyStatus}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-teal-950/30 border-l-4 border-teal-500 text-teal-200 p-3.5 rounded-r-lg mb-4 flex items-center gap-3 shadow-sm">
      <ShieldCheck className="w-5 h-5 text-teal-400 shrink-0" />
      <div className="text-sm">
        <span className="font-semibold text-teal-300">Safety Status: </span>
        <span className="text-teal-100">{safetyStatus}</span>
      </div>
    </div>
  );
};
