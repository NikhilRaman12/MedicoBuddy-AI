/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#0f172a",
          800: "#1e293b",
          700: "#334155",
          600: "#475569",
        },
        teal: {
          DEFAULT: "#0d9488",
          light: "#14b8a6",
          dark: "#0f766e",
        },
        saffron: {
          DEFAULT: "#d97706",
          light: "#f59e0b",
        },
        alert: {
          DEFAULT: "#ef4444",
          light: "#f87171",
        },
      },
    },
  },
  plugins: [],
};
