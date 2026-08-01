import React from "react";
import { MessageItem } from "../../state/useStore";
import { MessageCard } from "./MessageCard";
import { StarterCards } from "./StarterCards";

interface MessageListProps {
  messages: MessageItem[];
  onSelectQuery: (query: string) => void;
  isGenerating: boolean;
  currentStageMessage?: string;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  onSelectQuery,
  isGenerating,
  currentStageMessage = "Running GraphRAG retrieval & evidence validation...",
}) => {
  const listEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isGenerating, currentStageMessage]);

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
      {messages.length === 0 ? (
        <StarterCards onSelect={onSelectQuery} />
      ) : (
        messages.map((msg) => (
          <MessageCard key={msg.id} message={msg} onSelectFollowUp={onSelectQuery} />
        ))
      )}

      {isGenerating && (
        <div className="bg-navy-800 border border-teal-800/60 p-4 rounded-xl flex items-center gap-3 text-sm text-teal-300 animate-pulse shadow-sm">
          <div className="w-4 h-4 rounded-full border-2 border-teal-400 border-t-transparent animate-spin" />
          <span>🔄 {currentStageMessage}</span>
        </div>
      )}

      <div ref={listEndRef} />
    </div>
  );
};
