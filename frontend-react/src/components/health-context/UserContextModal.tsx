import React from "react";
import { User, ShieldAlert, Check } from "lucide-react";
import { useStore } from "../../state/useStore";

const CHRONIC_OPTIONS = [
  "Hypertension",
  "Diabetes Type 2",
  "Asthma",
  "Thyroid Disorder",
  "GERD / Acid Reflux",
  "Kidney Disease",
];

export const UserContextModal: React.FC = () => {
  const { userContext, setUserContext } = useStore();

  const handleAgeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setUserContext({ age_range: e.target.value });
  };

  const handlePregnancyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setUserContext({ pregnancy_status: e.target.value });
  };

  const handleChronicToggle = (condition: string) => {
    const current = userContext.chronic_conditions || [];
    const updated = current.includes(condition)
      ? current.filter((c) => c !== condition)
      : [...current, condition];
    setUserContext({ chronic_conditions: updated });
  };

  return (
    <div className="space-y-3.5 text-xs text-slate-300">
      <div className="flex items-center gap-2 text-teal-300 font-semibold border-b border-navy-700 pb-2">
        <User className="w-4 h-4 text-teal-400" />
        <span>User Health Context</span>
      </div>

      {/* Age Group */}
      <div>
        <label className="block text-slate-400 mb-1 font-medium">Age Group</label>
        <select
          value={userContext.age_range}
          onChange={handleAgeChange}
          className="w-full bg-navy-900 border border-navy-700 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-teal-500"
        >
          <option value="18_65">Adults 18–65 (Target Population)</option>
          <option value="under_18">Youth (Under 18)</option>
          <option value="over_65">Seniors (Over 65)</option>
        </select>
      </div>

      {/* Pregnancy Status (Exact Enums: Unknown/Not Pregnant MUST never map to pregnant) */}
      <div>
        <label className="block text-slate-400 mb-1 font-medium">
          Pregnancy / Breastfeeding Status
        </label>
        <select
          value={userContext.pregnancy_status}
          onChange={handlePregnancyChange}
          className="w-full bg-navy-900 border border-navy-700 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-teal-500"
        >
          <option value="not_pregnant">Not Pregnant / Not Applicable</option>
          <option value="pregnant">Currently Pregnant</option>
          <option value="breastfeeding">Currently Breastfeeding</option>
          <option value="unknown">Unknown / Prefer not to say</option>
        </select>
      </div>

      {/* Chronic Conditions */}
      <div>
        <label className="block text-slate-400 mb-1 font-medium">
          Chronic Conditions (Optional)
        </label>
        <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
          {CHRONIC_OPTIONS.map((cond) => {
            const isSelected = (userContext.chronic_conditions || []).includes(cond);
            return (
              <button
                type="button"
                key={cond}
                onClick={() => handleChronicToggle(cond)}
                className={`w-full text-left p-1.5 rounded-lg border text-xs flex items-center justify-between transition-colors ${
                  isSelected
                    ? "bg-teal-950/60 border-teal-700 text-teal-200"
                    : "bg-navy-900 border-navy-700 text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>{cond}</span>
                {isSelected && <Check className="w-3.5 h-3.5 text-teal-400" />}
              </button>
            );
          })}
        </div>
      </div>

      <div className="bg-navy-900/60 p-2 rounded border border-navy-700/60 text-[11px] text-slate-400 flex items-start gap-1.5">
        <ShieldAlert className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
        <span>Context is used solely during this session to filter contraindications.</span>
      </div>
    </div>
  );
};
