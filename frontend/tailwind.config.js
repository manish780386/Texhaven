/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0C2231",
        tide: "#17394D",
        foam: "#EDF3F1",
        beam: "#F5A623",
        kelp: "#1E8E6E",
        buoy: "#D8432F",
        mist: "#9FB4BE",
        muted: "#4A6270",
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"Instrument Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      keyframes: {
        sweep: {
          "0%": { transform: "translateY(-10%)", opacity: "0" },
          "15%": { opacity: "1" },
          "85%": { opacity: "1" },
          "100%": { transform: "translateY(110%)", opacity: "0" },
        },
      },
      animation: { sweep: "sweep 2.4s ease-in-out 0.4s 1 both" },
    },
  },
  plugins: [],
};
