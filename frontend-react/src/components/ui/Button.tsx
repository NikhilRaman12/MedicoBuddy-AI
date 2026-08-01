import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  className = "",
  disabled,
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500/50 disabled:opacity-50 disabled:cursor-not-allowed";

  const variantStyles = {
    primary: "bg-teal-600 hover:bg-teal-500 text-white shadow-sm",
    secondary: "bg-navy-700 hover:bg-navy-600 text-slate-200 border border-navy-600",
    outline: "border border-navy-600 hover:bg-navy-800 text-slate-300",
    ghost: "hover:bg-navy-800 text-slate-300",
    danger: "bg-red-600 hover:bg-red-500 text-white shadow-sm",
  };

  const sizeStyles = {
    sm: "px-2.5 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-5 py-2.5 text-base",
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
