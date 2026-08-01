import React from "react";
import {
  Globe,
  Plus,
  Trash2,
  Sliders,
  ChevronRight,
  ChevronDown,
  Activity,
  Code,
} from "lucide-react";
import { useStore } from "../../state/useStore";
import { LANGUAGES } from "../../i18n";
import { UserContextModal } from "../health-context/UserContextModal";
import { getHealthReady, getHealthDependencies } from "../../api/health";

export const Sidebar: React.FC = () => {
  const {
    sidebarOpen,
    resetConversation,
    selectedLanguage,
    setSelectedLanguage,
    highContrast,
    setHighContrast,
  } = useStore();


  const [diagnosticsOpen, setDiagnosticsOpen] = React.useState(false);
  const [readyData, setReadyData] = React.useState<any>(null);
  const [depsData, setDepsData] = React.useState<any>(null);

  React.useEffect(() => {
    if (diagnosticsOpen) {
      Promise.all([getHealthReady(), getHealthDependencies()]).then(([r, d]) => {
        setReadyData(r);
        setDepsData(d);
      });
    }
  }, [diagnosticsOpen]);

  if (!sidebarOpen) return null;

  return (
    <aside className="w-72 bg-navy-800 border-r border-navy-700 flex flex-col h-[calc(100vh-3.5rem)] shrink-0 overflow-y-auto">
      <div className="p-4 space-y-5 flex-1">
        {/* New Conversation Button */}
        <button
          onClick={resetConversation}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-medium text-sm transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </button>

        {/* Multilingual Selector */}
        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Globe className="w-3.5 h-3.5 text-teal-400" />
            Language / 🇮🇳 ભાષા / 🇮🇳 భాష
          </label>
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="w-full bg-navy-900 border border-navy-700 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
          >
            {Object.entries(LANGUAGES).map(([code, info]) => (
              <option key={code} value={code}>
                {info.label}
              </option>
            ))}
          </select>
        </div>

        {/* User Context Section */}
        <div className="bg-navy-900/60 p-3 rounded-xl border border-navy-700/80">
          <UserContextModal />
        </div>

        {/* Preferences & Privacy Controls */}
        <div className="space-y-2 pt-2 border-t border-navy-700/60 text-xs text-slate-300">
          <div className="font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <Sliders className="w-3.5 h-3.5 text-teal-400" />
            Preferences & Privacy
          </div>

          <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
            <input
              type="checkbox"
              checked={highContrast}
              onChange={(e) => setHighContrast(e.target.checked)}
              className="rounded bg-navy-900 border-navy-700 text-teal-600 focus:ring-teal-500"
            />
            <span>High Contrast Mode</span>
          </label>

          <button
            onClick={resetConversation}
            className="w-full text-left flex items-center gap-2 py-1 text-red-400 hover:text-red-300 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Conversation History</span>
          </button>
        </div>

        {/* Admin Diagnostics (Protected behind expander) */}
        <div className="pt-2 border-t border-navy-700/60">
          <button
            onClick={() => setDiagnosticsOpen(!diagnosticsOpen)}
            className="w-full flex items-center justify-between text-xs text-slate-400 hover:text-slate-200 py-1"
          >
            <span className="flex items-center gap-1.5 font-medium">
              <Code className="w-3.5 h-3.5 text-slate-500" />
              Admin Diagnostics
            </span>
            {diagnosticsOpen ? (
              <ChevronDown className="w-3.5 h-3.5" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" />
            )}
          </button>

          {diagnosticsOpen && (
            <div className="mt-2 p-2.5 bg-navy-900 rounded-lg border border-navy-700 text-[11px] font-mono space-y-2 text-slate-300">
              <div className="flex items-center justify-between font-sans text-xs text-teal-300 font-semibold">
                <span>System Readiness</span>
                <Activity className="w-3 h-3 text-teal-400" />
              </div>
              <pre className="text-[10px] text-slate-400 overflow-x-auto">
                {JSON.stringify(readyData, null, 2)}
              </pre>

              <div className="font-sans text-xs text-teal-300 font-semibold pt-1 border-t border-navy-800">
                Dependencies Status
              </div>
              <pre className="text-[10px] text-slate-400 overflow-x-auto">
                {JSON.stringify(depsData, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
