import React from "react";
import { Info } from "lucide-react";

export const Disclaimer: React.FC = () => {
  return (
    <div className="mt-6 pt-4 border-t border-navy-700/60 text-xs text-slate-400 flex items-start gap-2">
      <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
      <p>
        <span className="font-semibold text-slate-300">Educational-Use Notice:</span>{" "}
        MedicoBuddy AI provides evidence-grounded general self-care education for adults aged
        18–65 with mild, short-duration concerns. It does not diagnose, prescribe, recommend
        medicines, or replace evaluation by a qualified healthcare professional.
      </p>
    </div>
  );
};
