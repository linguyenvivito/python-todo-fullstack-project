import daisyui from "daisyui";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Manrope", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        panel: "0 12px 30px -12px rgba(15, 23, 42, 0.35)",
      },
    },
  },
  plugins: [daisyui],
  daisyui: {
    themes: [
      {
        fluxboard: {
          primary: "#0f766e",
          secondary: "#ea580c",
          accent: "#0891b2",
          neutral: "#1f2937",
          "base-100": "#f7faf9",
          "base-200": "#ecf2ef",
          "base-300": "#d7e2dd",
          "base-content": "#0f172a",
          info: "#0369a1",
          success: "#15803d",
          warning: "#c2410c",
          error: "#be123c",
        },
      },
      {
        harbor: {
          primary: "#1d4ed8",
          secondary: "#0f766e",
          accent: "#ea580c",
          neutral: "#1e293b",
          "base-100": "#f8fafc",
          "base-200": "#eef2f7",
          "base-300": "#dbe4ef",
          "base-content": "#0f172a",
          info: "#0284c7",
          success: "#16a34a",
          warning: "#d97706",
          error: "#dc2626",
        },
      },
      {
        lagoon: {
          primary: "#0e7490",
          secondary: "#15803d",
          accent: "#2563eb",
          neutral: "#1f2937",
          "base-100": "#e6f4f1",
          "base-200": "#d6ece7",
          "base-300": "#bfded7",
          "base-content": "#0f172a",
          info: "#0369a1",
          success: "#15803d",
          warning: "#b45309",
          error: "#b91c1c",
        },
      },
      "corporate",
      "light",
    ],
    darkTheme: "corporate",
  },
};
