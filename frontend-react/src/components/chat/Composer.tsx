import React from "react";
import { Send, Square } from "lucide-react";

interface ComposerProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  isGenerating: boolean;
  placeholder?: string;
}

export const Composer: React.FC<ComposerProps> = ({
  onSend,
  onStop,
  isGenerating,
  placeholder = "Ask MedicoBuddy AI a health question in any language...",
}) => {
  const [text, setText] = React.useState("");

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!text.trim() || isGenerating) return;
    onSend(text.trim());
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="sticky bottom-0 bg-navy-900/95 backdrop-blur border-t border-navy-700/80 p-3 sm:p-4 z-20">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex items-end gap-2">
        <div className="flex-1 bg-navy-800 border border-navy-700 focus-within:border-teal-500 rounded-xl p-2 transition-colors">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={2}
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-400 focus:outline-none resize-none"
          />
        </div>

        {isGenerating ? (
          <button
            type="button"
            onClick={onStop}
            className="h-11 px-4 rounded-xl bg-red-600 hover:bg-red-500 text-white font-medium text-xs flex items-center justify-center gap-1.5 transition-colors shadow-sm shrink-0"
            title="Stop Generation"
          >
            <Square className="w-4 h-4 fill-current" />
            <span className="hidden sm:inline">Stop</span>
          </button>
        ) : (
          <button
            type="submit"
            disabled={!text.trim()}
            className="h-11 px-4 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:bg-navy-800 disabled:border disabled:border-navy-700 disabled:text-slate-500 text-white font-medium text-xs flex items-center justify-center gap-1.5 transition-colors shadow-sm shrink-0"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        )}
      </form>
    </div>
  );
};
