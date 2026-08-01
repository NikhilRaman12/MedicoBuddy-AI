import React from "react";
import { ActionTableRow } from "../../api/schemas";

interface ActionTableProps {
  rows: ActionTableRow[];
}

export const ActionTable: React.FC<ActionTableProps> = ({ rows }) => {
  if (!rows || rows.length === 0) return null;

  return (
    <div className="my-5">
      <h3 className="text-base font-semibold text-slate-100 mb-3 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-teal-400"></span>
        Responsive Action Table
      </h3>

      {/* Desktop & Tablet Table View */}
      <div className="hidden md:block overflow-x-auto rounded-xl border border-navy-700 bg-navy-800/80 shadow-sm">
        <table className="w-full text-left text-sm text-slate-200">
          <thead className="bg-navy-900/90 text-teal-400 font-semibold border-b border-navy-700 text-xs uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3">Guidance</th>
              <th className="px-4 py-3">What May Help</th>
              <th className="px-4 py-3">How to Follow</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3">Evidence</th>
              <th className="px-4 py-3">Cautions</th>
              <th className="px-4 py-3">Seek Care If</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-700/60">
            {rows.map((r, idx) => (
              <tr key={idx} className="hover:bg-navy-700/50 transition-colors">
                <td className="px-4 py-3 font-medium text-teal-300">{r.guidance_lens}</td>
                <td className="px-4 py-3">{r.what_may_help}</td>
                <td className="px-4 py-3 text-slate-300">{r.how_to_follow}</td>
                <td className="px-4 py-3 text-slate-400 text-xs">{r.frequency_duration}</td>
                <td className="px-4 py-3 text-xs">
                  <span className="inline-block px-2 py-0.5 rounded bg-teal-950/60 border border-teal-800 text-teal-300">
                    {r.evidence_strength}
                  </span>
                </td>
                <td className="px-4 py-3 text-amber-300/90 text-xs">{r.cautions}</td>
                <td className="px-4 py-3 text-red-300/90 text-xs">{r.stop_and_seek_care_if}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Stacked Action Cards */}
      <div className="md:hidden space-y-3">
        {rows.map((r, idx) => (
          <div
            key={idx}
            className="bg-navy-800 border border-navy-700 rounded-xl p-4 space-y-2 text-sm shadow-sm"
          >
            <div className="flex items-center justify-between border-b border-navy-700 pb-2">
              <span className="font-semibold text-teal-300">{r.guidance_lens}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-teal-950/60 border border-teal-800 text-teal-300">
                {r.evidence_strength}
              </span>
            </div>

            {r.what_may_help && (
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase">What May Help</span>
                <span className="text-slate-100">{r.what_may_help}</span>
              </div>
            )}

            {r.how_to_follow && (
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase">How to Follow</span>
                <span className="text-slate-300">{r.how_to_follow}</span>
              </div>
            )}

            {r.frequency_duration && (
              <div className="text-xs text-slate-400">
                <span className="font-semibold text-slate-400">Duration: </span>
                {r.frequency_duration}
              </div>
            )}

            {r.cautions && (
              <div className="text-xs text-amber-300/90 bg-amber-950/30 p-2 rounded border border-amber-900/40">
                <span className="font-semibold block">Caution:</span> {r.cautions}
              </div>
            )}

            {r.stop_and_seek_care_if && (
              <div className="text-xs text-red-300/90 bg-red-950/30 p-2 rounded border border-red-900/40">
                <span className="font-semibold block">Seek Care If:</span> {r.stop_and_seek_care_if}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
