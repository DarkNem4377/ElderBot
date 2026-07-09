/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // DisasterIQ brand tokens — mirrored in Logo.tsx and src/app/icon.svg
        diq: {
          navy: "#4C6BA8", // steel navy (dark-bg variant of logo navy #1B2A4A)
          orange: "#F08A1D",
          red: "#DC3B2A",
          bg: "#0A0F1F", // rich black, blue tint — page background
          panel: "#16213E", // arctic night — panel surfaces
          line: "#274C77", // dark steel blue — borders and rules
        },
      },
      fontFamily: {
        label: [
          "ui-monospace",
          "JetBrains Mono",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};