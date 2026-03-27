import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        abyss: "#05070d",
        panel: "#0b111f",
        neon: "#d4ff00",
        cyan: "#00eaff",
        ink: "#e8edf4",
        muted: "#8390a6",
      },
      fontFamily: {
        display: ["Orbitron", "sans-serif"],
        body: ["Rajdhani", "sans-serif"],
      },
      boxShadow: {
        neon: "0 0 28px rgba(212, 255, 0, 0.38)",
        cyan: "0 0 24px rgba(0, 234, 255, 0.22)",
        glass: "0 0 28px rgba(0, 0, 0, 0.4), inset 0 0 26px rgba(255, 255, 255, 0.02)",
      },
      backgroundImage: {
        grid:
          "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
} satisfies Config;
