/**
 * Global application configuration.
 */

export const THEME_STORAGE_KEY = "fluxboard.ui.theme";

export const THEME_OPTIONS = ["fluxboard", "harbor", "lagoon", "light", "corporate"] as const;

export type ThemeOption = (typeof THEME_OPTIONS)[number];

export function getInitialTheme(): ThemeOption {
  if (typeof window === "undefined") {
    return "fluxboard";
  }

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  return THEME_OPTIONS.includes(storedTheme as ThemeOption) ? (storedTheme as ThemeOption) : "fluxboard";
}

export function saveTheme(theme: ThemeOption): void {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }
}
