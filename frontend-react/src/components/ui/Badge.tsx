import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "green" | "amber" | "red" | "neutral" | "saffron";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "neutral",
  className = "",
}) => {
  const variantStyles = {
    green: "bg-teal-950/60 text-teal-400 border-teal-800",
    amber: "bg-amber-950/60 text-amber-400 border-amber-800",
    red: "bg-red-950/60 text-red-400 border-red-800",
    saffron: "bg-amber-950/40 text-saffron-light border-saffron/40",
    neutral: "bg-slate-800 text-slate-300 border-slate-700",
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
