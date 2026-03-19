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

export interface OmniSettings {
  // Theme
  theme: ThemeName;
  accentColor: "sky" | "violet" | "emerald" | "rose" | "amber" | "cyan";
  backgroundImage: string; // URL for translucent theme

  // UI toggles
  showThumbnails: boolean;
  showDescriptions: boolean;
  showViewCount: boolean;
  showLikeCount: boolean;
  showChannelAvatar: boolean;

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
  backgroundImage: "",
  showThumbnails: true,
  showDescriptions: false,
  showViewCount: true,
  showLikeCount: false,
  showChannelAvatar: true,
  showVideoDescription: true,
  showVideoComments: true,
  theaterMode: false,
  defaultQuality: 720,
  feedPerPage: 30,
};

const STORAGE_KEY = "omnitube-settings";

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
