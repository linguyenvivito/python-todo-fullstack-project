/**
 * SidebarLayout: Shared layout component with navigation sidebar.
 * Contains the app shell (sidebar, main content area, theme switcher, logout button).
 */

import React from "react";
import { THEME_OPTIONS, ThemeOption } from "../config";
import { MENU_ITEMS, PageId } from "../routes/navigation";

interface SidebarLayoutProps {
  authUser: string;
  currentPage: PageId;
  theme: ThemeOption;
  onNavigate: (page: PageId) => void;
  onThemeChange: (theme: ThemeOption) => void;
  onLogout: () => void;
  children: React.ReactNode;
}

export function SidebarLayout({
  authUser,
  currentPage,
  theme,
  onNavigate,
  onThemeChange,
  onLogout,
  children,
}: SidebarLayoutProps) {
  return (
    <div className="mx-auto w-full max-w-[1440px] px-3 py-4 sm:px-6 lg:px-8">
      <div className="grid gap-4 lg:grid-cols-[280px_minmax(760px,1fr)] lg:gap-6">
        {/* Sidebar */}
        <aside className="card border border-base-200 shadow-xl lg:sticky lg:top-4 lg:h-[calc(100vh-2rem)]">
          <div className="card-body p-5">
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-primary">
              Task Management API
            </p>
            <h1 className="text-2xl font-bold tracking-tight">Fluxboard</h1>
            <small className="font-mono text-xs text-base-content/60">v0.6</small>

            {/* User info */}
            <div className="mt-2 rounded-xl border border-base-300 bg-base-200 px-3 py-2">
              <p className="font-mono text-[11px] uppercase tracking-wide text-base-content/70">Signed in as</p>
              <p className="truncate text-sm font-semibold text-base-content">{authUser}</p>
            </div>

            {/* Navigation */}
            <nav className="mt-3 grid gap-2">
              {MENU_ITEMS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onNavigate(item.id)}
                  className={`btn justify-start ${
                    currentPage === item.id ? "btn-primary" : "btn-ghost border border-base-300"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </nav>

            {/* Theme selector and logout */}
            <div className="mt-auto grid space-y-3">
              <label className="form-control rounded-xl border border-base-300 p-2">
                <span className="label pb-1 pt-0">
                  <span className="label-text font-mono text-[11px] uppercase tracking-wide text-base-content/70">
                    Theme
                  </span>
                </span>
                <select
                  className="select select-bordered select-sm"
                  value={theme}
                  onChange={(event) => onThemeChange(event.target.value as ThemeOption)}
                >
                  <option value="fluxboard">Fluxboard</option>
                  <option value="harbor">Harbor</option>
                  <option value="lagoon">Lagoon</option>
                  <option value="light">Light</option>
                  <option value="corporate">Corporate</option>
                </select>
              </label>

              <button type="button" onClick={onLogout} className="btn btn-primary w-full">
                Logout
              </button>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="mx-auto w-full max-w-5xl">{children}</main>
      </div>
    </div>
  );
}
