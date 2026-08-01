import React from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { EvidenceDrawer } from "../evidence/EvidenceDrawer";
import { useStore } from "../../state/useStore";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { messages, activeDrawerMessageId, setActiveDrawerMessageId } = useStore();


  const activeMessage = React.useMemo(() => {
    if (!activeDrawerMessageId) return null;
    return messages.find((m) => m.id === activeDrawerMessageId) || null;
  }, [messages, activeDrawerMessageId]);

  return (
    <div className="h-screen flex flex-col bg-navy-900 text-slate-100 overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 bg-navy-900 relative">
          {children}
        </main>
        <EvidenceDrawer
          data={activeMessage?.data || null}
          requestId={activeMessage?.requestId || ""}
          isOpen={!!activeDrawerMessageId}
          onClose={() => setActiveDrawerMessageId(null)}
        />
      </div>
    </div>
  );
};
