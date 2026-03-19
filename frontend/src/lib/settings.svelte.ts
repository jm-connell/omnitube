/**
 * Settings store — persisted in localStorage.
 *
 * Controls theme, UI toggles, and display preferences.
 * All data lives locally — nothing is sent to a server.
 */

import { browser } from "$app/environment";

export type ThemeName =
  | "dark-blue"
  | "oled"
  | "very-dark"
  | "hacker-green"
  | "translucent"
  | "macos"
  | "nord"
  | "solarized"
  | "light";

export type AccentColor =
  | "sky"
  | "violet"
  | "emerald"
  | "rose"
  | "amber"
  | "cyan"
  | "custom";

export interface OmniSettings {
  // Theme
  theme: ThemeName;
  accentColor: AccentColor;
  customAccentColor: string; // hex color for custom accent
  favoriteColors: string[]; // saved custom hex colors
  backgroundImage: string; // URL for translucent theme

  // Translucent theme controls
  translucentBlur: number; // backdrop blur in px (0-30)
  translucentTint: number; // tint opacity 0-100
  translucentTintColor: string; // hex color for the glass tint
  translucentBlurMode: "elements" | "page"; // blur on elements or full page

  // UI toggles
  showThumbnails: boolean;
  showDescriptions: boolean;
  showViewCount: boolean;
  showLikeCount: boolean;
  showChannelAvatar: boolean;
  showLivestreams: boolean;

  // Video page
  showVideoDescription: boolean;
  showVideoComments: boolean;
  theaterMode: boolean;
  defaultQuality: number; // 0 = highest available

  // Feed
  feedPerPage: number;
}

export const THEME_META: Record<
  ThemeName,
  { label: string; description: string }
> = {
  "dark-blue": {
    label: "Dark Blue",
    description: "Default — Hyprland-inspired blue-gray",
  },
  oled: {
    label: "OLED Certified",
    description: "True-black background, saves battery on OLED",
  },
  "very-dark": {
    label: "Very Dark",
    description: "Dark navy, not quite black",
  },
  "hacker-green": {
    label: "Hacker Green",
    description: "Terminal vibes — green on black, all mono",
  },
  translucent: {
    label: "Translucent",
    description: "Frosted glass over your background image",
  },
  macos: {
    label: "macOS",
    description: "Clean Apple-inspired design",
  },
  nord: {
    label: "Nord",
    description: "Arctic, north-bluish color palette",
  },
  solarized: {
    label: "Solarized Dark",
    description: "Ethan Schoonover's precision color scheme",
  },
  light: {
    label: "Light",
    description: "Bright & minimal",
  },
};

const DEFAULTS: OmniSettings = {
  theme: "dark-blue",
  accentColor: "sky",
  customAccentColor: "#7dd3fc",
  favoriteColors: [],
  backgroundImage: "",
  translucentBlur: 12,
  translucentTint: 50,
  translucentTintColor: "#0f172a",
  translucentBlurMode: "elements",
  showThumbnails: true,
  showDescriptions: false,
  showViewCount: true,
  showLikeCount: false,
  showChannelAvatar: true,
  showLivestreams: true,
  showVideoDescription: true,
  showVideoComments: true,
  theaterMode: false,
  defaultQuality: 720,
  feedPerPage: 30,
};

const STORAGE_KEY = "omnitube-settings";

/** Darken a hex color by a percentage (0-100). */
function darkenHex(hex: string, percent: number): string {
  const num = parseInt(hex.replace("#", ""), 16);
  const r = Math.max(0, ((num >> 16) & 0xff) - Math.round(2.55 * percent));
  const g = Math.max(0, ((num >> 8) & 0xff) - Math.round(2.55 * percent));
  const b = Math.max(0, (num & 0xff) - Math.round(2.55 * percent));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
}

function loadSettings(): OmniSettings {
  if (!browser) return { ...DEFAULTS };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      // Migrate old theme values
      if (parsed.theme === "dark") parsed.theme = "dark-blue";
      return { ...DEFAULTS, ...parsed };
    }
  } catch {
    // Corrupted storage; reset
  }
  return { ...DEFAULTS };
}

function saveSettings(s: OmniSettings) {
  if (!browser) return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

/**
 * Reactive settings using Svelte 5 runes ($state).
 */
function createSettings() {
  let settings = $state<OmniSettings>(loadSettings());

  function applyTheme() {
    if (!browser) return;
    const html = document.documentElement;

    // Remove all theme classes
    const themeClasses = Object.keys(THEME_META).map((t) => `theme-${t}`);
    html.classList.remove(...themeClasses, "dark", "light");

    // Apply new theme class
    html.classList.add(`theme-${settings.theme}`);

    // Also set light/dark for browser chrome (scrollbars etc.)
    html.classList.add(
      settings.theme === "light" || settings.theme === "macos"
        ? "light"
        : "dark",
    );

    // Accent color
    html.className = html.className.replace(/accent-\w+/g, "").trim();
    html.classList.add(`accent-${settings.accentColor}`);

    // Custom accent: set CSS custom properties directly
    if (settings.accentColor === "custom" && settings.customAccentColor) {
      const hex = settings.customAccentColor;
      html.style.setProperty("--omni-accent", hex);
      // Darken slightly for hover
      html.style.setProperty("--omni-accent-hover", darkenHex(hex, 15));
    } else {
      html.style.removeProperty("--omni-accent");
      html.style.removeProperty("--omni-accent-hover");
    }

    // Translucent theme settings
    if (settings.theme === "translucent") {
      html.style.setProperty("--glass-blur", `${settings.translucentBlur}px`);
      html.style.setProperty(
        "--glass-tint",
        `${settings.translucentTint / 100}`,
      );
      html.style.setProperty(
        "--glass-tint-color",
        settings.translucentTintColor || "#0f172a",
      );
      html.classList.toggle(
        "glass-page-blur",
        settings.translucentBlurMode === "page",
      );
    } else {
      html.style.removeProperty("--glass-blur");
      html.style.removeProperty("--glass-tint");
      html.style.removeProperty("--glass-tint-color");
      html.classList.remove("glass-page-blur");
    }

    // Background image for translucent theme
    if (settings.theme === "translucent" && settings.backgroundImage) {
      document.body.style.backgroundImage = `url(${CSS.escape(settings.backgroundImage)})`;
      document.body.style.backgroundSize = "cover";
      document.body.style.backgroundPosition = "center";
      document.body.style.backgroundAttachment = "fixed";
    } else {
      document.body.style.backgroundImage = "";
      document.body.style.backgroundSize = "";
      document.body.style.backgroundPosition = "";
      document.body.style.backgroundAttachment = "";
    }
  }

  function update(partial: Partial<OmniSettings>) {
    settings = { ...settings, ...partial };
    saveSettings(settings);
    applyTheme();
  }

  function reset() {
    settings = { ...DEFAULTS };
    saveSettings(settings);
    applyTheme();
  }

  // Apply theme on init
  if (browser) {
    applyTheme();
  }

  return {
    get current() {
      return settings;
    },
    update,
    reset,
    applyTheme,
  };
}

export const settingsStore = createSettings();
