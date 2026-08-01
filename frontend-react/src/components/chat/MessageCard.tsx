import React from "react";
import { User, Bot, Download, ThumbsUp, ThumbsDown, Search, Check } from "lucide-react";
import { MessageItem, useStore } from "../../state/useStore";
import { SafetyBanner } from "../safety/SafetyBanner";
import { ActionTable } from "./ActionTable";
import { FollowUpChips } from "./FollowUpChips";
import { Disclaimer } from "../safety/Disclaimer";

interface MessageCardProps {
  message: MessageItem;
  onSelectFollowUp: (query: string) => void;
}

export const MessageCard: React.FC<MessageCardProps> = ({ message, onSelectFollowUp }) => {
  const { setActiveDrawerMessageId } = useStore();
  const [copied, setCopied] = React.useState(false);
  const [feedbackSent, setFeedbackSent] = React.useState(false);

  const isUser = message.role === "user";
  const data = message.data;

  const handleDownloadReport = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `medicobuddy_report_${message.id.slice(0, 8)}.json`;
    a.click();
  };

  const handleCopy = () => {
    const textToCopy = data?.summary || message.content;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`p-4 sm:p-5 rounded-2xl border transition-all ${
        isUser
          ? "bg-navy-800/80 border-navy-700 ml-auto max-w-2xl text-slate-100"
          : "bg-navy-800 border-navy-700 text-slate-100 shadow-sm"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3 text-xs text-slate-400">
        <div className="flex items-center gap-2 font-medium">
          {isUser ? (
            <>
              <div className="w-6 h-6 rounded-full bg-teal-900/80 border border-teal-700 text-teal-300 flex items-center justify-center">
                <User className="w-3.5 h-3.5" />
              </div>
              <span className="text-slate-200">You</span>
            </>
          ) : (
            <>
              <div className="w-6 h-6 rounded-full bg-teal-600 text-white flex items-center justify-center shadow-sm">
                <Bot className="w-3.5 h-3.5" />
              </div>
              <span className="text-teal-300 font-semibold">MedicoBuddy AI</span>
            </>
          )}
        </div>
        <span className="text-[11px] text-slate-500">{message.timestamp}</span>
      </div>

      {/* User Query Content */}
      {isUser ? (
        <p className="text-sm text-slate-100 leading-relaxed">{message.content}</p>
      ) : data ? (
        /* Structured Assistant Response Order */
        <div className="space-y-4 text-sm text-slate-200">
          {/* 1. Safety Status Banner */}
          <SafetyBanner
            safetyStatus={data.safety_status}
            triageOutcome={data.triage_outcome}
          />

          {/* 2. Scope Statement */}
          {data.what_this_applies_to && (
            <p className="text-xs text-slate-400">
              <span className="font-semibold text-slate-300">Scope:</span> {data.what_this_applies_to}
            </p>
          )}

          {/* 3. Plain-Language Summary */}
          {data.summary && (
            <div>
              <h3 className="text-base font-semibold text-slate-100 mb-1.5">
                Summary Guidance
              </h3>
              <p className="text-slate-200 leading-relaxed">{data.summary}</p>
            </div>
          )}

          {/* 4. Responsive Action Table */}
          <ActionTable rows={data.action_table || []} />

          {/* 5. Preventive Approaches */}
          {data.preventive_approaches && data.preventive_approaches.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-200 mb-1.5">
                Natural Preventive Approaches
              </h4>
              <ul className="list-disc list-inside space-y-1 text-xs text-slate-300">
                {data.preventive_approaches.map((p, idx) => (
                  <li key={idx}>🌱 {p}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 6. Traditional Ayurvedic Context */}
          {data.ayurveda_perspectives && data.ayurveda_perspectives.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-saffron-light mb-1.5">
                Traditional Ayurvedic Context
              </h4>
              <div className="space-y-1.5 text-xs text-slate-300">
                {data.ayurveda_perspectives.map((a: any, idx: number) => (
                  <div key={idx} className="bg-navy-900/60 p-2.5 rounded border border-navy-700/60">
                    <span className="font-semibold text-saffron-light">{a.practice}</span>{" "}
                    <span className="text-[10px] text-slate-400">
                      [{a.evidence_label?.replace("_", " ")}]
                    </span>
                    : {a.description}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 7. Implementation Plan */}
          {data.implementation_plan &&
            (data.implementation_plan.now || data.implementation_plan.next_6_to_12_hours) && (
              <div className="bg-navy-900/80 p-3.5 rounded-xl border border-navy-700 space-y-2">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Implementation Plan
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                  {data.implementation_plan.now && (
                    <div className="bg-navy-800 p-2 rounded border border-navy-700">
                      <span className="text-[10px] text-teal-400 font-semibold block">NOW</span>
                      <span className="text-slate-200">{data.implementation_plan.now}</span>
                    </div>
                  )}
                  {data.implementation_plan.next_6_to_12_hours && (
                    <div className="bg-navy-800 p-2 rounded border border-navy-700">
                      <span className="text-[10px] text-teal-400 font-semibold block">NEXT 6–12 HOURS</span>
                      <span className="text-slate-200">{data.implementation_plan.next_6_to_12_hours}</span>
                    </div>
                  )}
                  {data.implementation_plan.next_24_to_48_hours && (
                    <div className="bg-navy-800 p-2 rounded border border-navy-700">
                      <span className="text-[10px] text-teal-400 font-semibold block">NEXT 24–48 HOURS</span>
                      <span className="text-slate-200">{data.implementation_plan.next_24_to_48_hours}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

          {/* 8. Things to Avoid */}
          {data.things_to_avoid && data.things_to_avoid.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-200 mb-1">Things to Avoid</h4>
              <ul className="list-disc list-inside space-y-1 text-xs text-slate-300">
                {data.things_to_avoid.map((av, idx) => (
                  <li key={idx}>🚫 {av}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 9. Warning Signs */}
          {((data.when_to_seek_care && data.when_to_seek_care.length > 0) ||
            (data.warning_signs && data.warning_signs.length > 0)) && (
            <div className="bg-red-950/20 p-3 rounded-xl border border-red-900/40 space-y-1">
              <h4 className="text-xs font-semibold text-red-300 uppercase tracking-wider">
                Warning Signs — When to Seek Care
              </h4>
              <ul className="list-disc list-inside space-y-0.5 text-xs text-red-200/90">
                {(data.when_to_seek_care || data.warning_signs || []).map((ws, idx) => (
                  <li key={idx}>⚠️ {ws}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 10. Clarification Question */}
          {(data.follow_up_question || data.targeted_follow_up) && (
            <p className="text-xs text-slate-300 font-medium italic bg-navy-900/60 p-2.5 rounded border border-navy-700/60">
              ❓ <span className="font-semibold text-slate-200">Clarifying Question:</span>{" "}
              {data.follow_up_question || data.targeted_follow_up}
            </p>
          )}

          {/* 11. Interactive Follow-up Actions */}
          <FollowUpChips
            actions={data.quick_actions || []}
            chips={data.quick_action_chips || []}
            onSelect={onSelectFollowUp}
          />

          {/* Controls Bar: Download Report, Open Evidence Drawer, Feedback */}
          <div className="mt-4 pt-3 border-t border-navy-700/60 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveDrawerMessageId(message.id)}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-navy-900 hover:bg-navy-700 border border-navy-700 text-teal-300 hover:text-teal-200 transition-colors"
              >
                <Search className="w-3.5 h-3.5 text-teal-400" />
                <span>Evidence Drawer ({data.citations?.length || 0})</span>
              </button>

              <button
                onClick={handleDownloadReport}
                className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-navy-900 hover:bg-navy-700 border border-navy-700 text-slate-300 hover:text-slate-100 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Report</span>
              </button>

              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-navy-900 hover:bg-navy-700 border border-navy-700 text-slate-300 hover:text-slate-100 transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-teal-400" /> : null}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setFeedbackSent(true)}
                className={`p-1.5 rounded hover:bg-navy-700 transition-colors ${
                  feedbackSent ? "text-teal-400" : "text-slate-400"
                }`}
                title="Helpful"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setFeedbackSent(true)}
                className="p-1.5 rounded hover:bg-navy-700 text-slate-400 transition-colors"
                title="Needs Improvement"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Educational Disclaimer Notice */}
          <Disclaimer />
        </div>
      ) : (
        <p className="text-sm text-slate-100 leading-relaxed">{message.content}</p>
      )}
    </div>
  );
};
