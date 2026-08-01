import React from "react";
import { MessageSquarePlus } from "lucide-react";
import { QuickAction } from "../../api/schemas";

interface FollowUpChipsProps {
  actions: QuickAction[];
  chips?: string[];
  onSelect: (standaloneQuery: string) => void;
}

export const FollowUpChips: React.FC<FollowUpChipsProps> = ({
  actions,
  chips = [],
  onSelect,
}) => {
  // Prefer structured quick_actions over raw string chips
  const actionList: { label: string; query: string }[] = [];

  if (actions && actions.length > 0) {
    actions.forEach((a) => {
      if (a.label) {
        actionList.push({
          label: a.label,
          query: a.standalone_query || a.label,
        });
      }
    });
  } else if (chips && chips.length > 0) {
    chips.forEach((c) => {
      if (typeof c === "string" && c.trim()) {
        actionList.push({ label: c, query: c });
      }
    });
  }

  if (actionList.length === 0) return null;

  return (
    <div className="mt-4 pt-3 border-t border-navy-700/60">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
        <MessageSquarePlus className="w-3.5 h-3.5 text-teal-400" />
        Suggested Follow-up Actions
      </h4>

      <div className="flex flex-wrap gap-2">
        {actionList.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(item.query)}
            className="text-xs text-teal-300 hover:text-white bg-navy-800 hover:bg-teal-900/60 border border-teal-800/60 hover:border-teal-500 rounded-lg px-3 py-2 text-left transition-all shadow-sm"
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
};
