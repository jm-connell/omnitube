/**
 * Settings store — persisted in localStorage.
 *
 * Controls theme, UI toggles, and display preferences.
 */

import { browser } from "$app/environment";

export interface OmniSettings {
  // Theme
  theme: "dark" | "light";
  accentColor: "sky" | "violet" | "emerald" | "rose" | "amber" | "cyan";

  // UI toggles
  showThumbnails: boolean;
  showDescriptions: boolean;
  showViewCount: boolean;
  showLikeCount: boolean;
  showChannelAvatar: boolean;

  // Feed
  feedPerPage: number;
}

const DEFAULTS: OmniSettings = {
  theme: "dark",
  accentColor: "sky",
  showThumbnails: true,
  showDescriptions: false,
  showViewCount: true,
  showLikeCount: false,
  showChannelAvatar: true,
  feedPerPage: 30,
};

const STORAGE_KEY = "omnitube-settings";

function loadSettings(): OmniSettings {
  if (!browser) return { ...DEFAULTS };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
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

    // Theme mode
    html.classList.remove("dark", "light");
    html.classList.add(settings.theme);

    // Accent color
    html.className = html.className.replace(/accent-\w+/g, "").trim();
    html.classList.add(`accent-${settings.accentColor}`);
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
