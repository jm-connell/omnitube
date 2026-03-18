/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // OmniTube Hyprland-inspired palette
        omni: {
          bg: "var(--omni-bg)",
          surface: "var(--omni-surface)",
          "surface-hover": "var(--omni-surface-hover)",
          border: "var(--omni-border)",
          text: "var(--omni-text)",
          "text-muted": "var(--omni-text-muted)",
          accent: "var(--omni-accent)",
          "accent-hover": "var(--omni-accent-hover)",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Cascadia Code", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
