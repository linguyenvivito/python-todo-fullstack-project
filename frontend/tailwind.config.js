import daisyui from "daisyui";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
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
          primary: "#22d3ee",
          secondary: "#fb7185",
          accent: "#c4b5fd",
          neutral: "#475569",
          "base-100": "#ffffff",
          "base-200": "#fcfdff",
          "base-300": "#f1f6ff",
          "base-content": "#0b1220",
          info: "#60a5fa",
          success: "#4ade80",
          warning: "#fbbf24",
          error: "#fb7185",
        },
      },
      "corporate",
      "light",
    ],
    darkTheme: "corporate",
  },
};
