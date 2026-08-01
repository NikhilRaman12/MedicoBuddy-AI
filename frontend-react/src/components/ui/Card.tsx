import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({ children, className = "", onClick }) => {
  return (
    <div
      onClick={onClick}
      className={`bg-navy-800 border border-navy-700 rounded-xl p-4 shadow-sm transition-all ${
        onClick ? "cursor-pointer hover:border-teal-500/50 hover:bg-navy-700/80" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
};
