import React from "react";
import { Menu, Plus, Activity } from "lucide-react";
import { useStore } from "../../state/useStore";
import { getHealthReady, getHealthDependencies } from "../../api/health";

export const Header: React.FC = () => {
  const { sidebarOpen, setSidebarOpen, resetConversation } = useStore();

  const [backendMode, setBackendMode] = React.useState<string>("LOCAL");
  const [healthStatus, setHealthStatus] = React.useState<"green" | "amber" | "red">("green");

  React.useEffect(() => {
    const checkStatus = async () => {
      const readyData = await getHealthReady();
      const depsData = await getHealthDependencies();

      setBackendMode(readyData.active_profile || "LOCAL");

      if (readyData.ready && readyData.vector_db === "connected") {
        setHealthStatus("green");
      } else if (
        readyData.vector_db === "local_faiss_fallback" ||
        depsData.overall === "degraded"
      ) {
        setHealthStatus("amber");
      } else {
        setHealthStatus("red");
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const badgeStyles = {
    green: "bg-teal-950/60 text-teal-400 border-teal-800",
    amber: "bg-amber-950/60 text-amber-400 border-amber-800",
    red: "bg-red-950/60 text-red-400 border-red-800",
  };

  const statusLabel = {
    green: `Mode: ${backendMode} (Ready)`,
    amber: "Mode: Degraded (Local FAISS Fallback)",
    red: "Mode: Service Offline",
  };

  return (
    <header className="h-14 bg-navy-800 border-b border-navy-700 px-4 flex items-center justify-between shrink-0 z-30">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-1.5 hover:bg-navy-700 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2">
          <img src="/logo.svg" alt="MedicoBuddy AI" className="w-7 h-7" />
          <h1 className="font-bold text-slate-100 text-base hidden sm:block">
            MedicoBuddy AI
          </h1>
          <span className="text-xs text-slate-400 hidden lg:block border-l border-navy-700 pl-3">
            Everyday health questions, connected to clearer evidence.
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend Mode Status Badge */}
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${badgeStyles[healthStatus]}`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>{statusLabel[healthStatus]}</span>
        </span>

        {/* New Conversation Button */}
        <button
          onClick={resetConversation}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-medium transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">New Conversation</span>
        </button>
      </div>
    </header>
  );
};
