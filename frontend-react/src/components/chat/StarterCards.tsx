import React from "react";
import { Thermometer, Brain, Sparkles, HeartPulse, Moon, Scissors } from "lucide-react";

interface StarterCard {
  id: string;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  query: string;
}

const STARTER_CARDS: StarterCard[] = [
  {
    id: "starter_cold",
    icon: <Thermometer className="w-5 h-5 text-teal-400" />,
    title: "Cold & Sore Throat",
    subtitle: "Natural remedies & congestion comfort",
    query: "I have a slight cold and sore throat for 2 days. What natural remedies and self-care measures help?",
  },
  {
    id: "starter_headache",
    icon: <Brain className="w-5 h-5 text-teal-400" />,
    title: "Headache",
    subtitle: "Tension headache self-care steps",
    query: "I have a mild tension headache since this morning. What evidence-based self-care steps can I take?",
  },
  {
    id: "starter_nausea",
    icon: <Sparkles className="w-5 h-5 text-teal-400" />,
    title: "Nausea",
    subtitle: "Post-meal stomach queasiness steps",
    query: "I am feeling mild nausea after eating lunch. What non-pharmacological comfort steps should I try?",
  },
  {
    id: "starter_digestive",
    icon: <HeartPulse className="w-5 h-5 text-teal-400" />,
    title: "Digestive Discomfort",
    subtitle: "Indigestion & bloating relief",
    query: "What natural self-care approaches help relieve mild bloating and digestive indigestion?",
  },
  {
    id: "starter_fatigue",
    icon: <Moon className="w-5 h-5 text-teal-400" />,
    title: "Fatigue",
    subtitle: "Sleep hygiene & daily energy boost",
    query: "I feel persistent tiredness after work. What sleep hygiene and nutrition practices boost daily energy?",
  },
  {
    id: "starter_hair",
    icon: <Scissors className="w-5 h-5 text-teal-400" />,
    title: "Hair & Scalp Care",
    subtitle: "Stress-related hair fall self-care",
    query: "What evidence-based self-care and nutrition measures help reduce stress-related hair fall?",
  },
];

interface StarterCardsProps {
  onSelect: (query: string) => void;
}

export const StarterCards: React.FC<StarterCardsProps> = ({ onSelect }) => {
  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-slate-300 mb-3">
        Select a health concern or type your question below:
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {STARTER_CARDS.map((card) => (
          <button
            key={card.id}
            onClick={() => onSelect(card.query)}
            className="text-left bg-navy-800 hover:bg-navy-700 border border-navy-700 hover:border-teal-500/50 p-3.5 rounded-xl transition-all group shadow-sm"
          >
            <div className="flex items-center gap-2.5 mb-1.5">
              <div className="p-1.5 rounded-lg bg-navy-900 border border-navy-700 group-hover:border-teal-500/30">
                {card.icon}
              </div>
              <span className="font-medium text-slate-100 text-sm">{card.title}</span>
            </div>
            <p className="text-xs text-slate-400 group-hover:text-slate-300 leading-snug">
              {card.subtitle}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
};
