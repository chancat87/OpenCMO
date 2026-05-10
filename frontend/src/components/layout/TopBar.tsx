import { ChevronDown, Globe, LogOut, Menu } from "lucide-react";
import { useAuth } from "../auth/useAuth";
import { useI18n } from "../../i18n";
import { LOCALE_LABELS, SUPPORTED_LOCALES, type Locale } from "../../i18n/locale";
import { NotificationBell } from "./NotificationBell";

export function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { isAuthenticated, logout } = useAuth();
  const { locale, setLocale, t } = useI18n();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between bg-white/80 px-4 backdrop-blur-xl transition-colors duration-500">
      <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-all hover:scale-105 active:scale-95 lg:hidden" onClick={onMenuClick}>
        <Menu size={20} />
      </button>
      <div className="flex-1" />
      <div className="flex items-center gap-3 pr-2 lg:pr-4">
        <NotificationBell />
        <label className="group relative flex items-center rounded-lg text-xs font-medium text-slate-500 transition-all duration-200 hover:bg-slate-100 hover:text-slate-900">
          <Globe size={16} className="pointer-events-none absolute left-3 transition-transform group-hover:rotate-12" />
          <select
            aria-label="Select language"
            value={locale}
            onChange={(event) => setLocale(event.target.value as Locale)}
            className="h-9 cursor-pointer appearance-none rounded-lg bg-transparent pl-9 pr-8 text-xs font-medium outline-none"
          >
            {SUPPORTED_LOCALES.map((item) => (
              <option key={item} value={item}>
                {LOCALE_LABELS[item]}
              </option>
            ))}
          </select>
          <ChevronDown size={14} className="pointer-events-none absolute right-2.5 text-slate-400" />
        </label>
        {isAuthenticated && (
          <button
            onClick={logout}
            className="group flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium text-slate-500 transition-all duration-200 hover:bg-slate-100 hover:text-slate-900 hover:scale-105 active:scale-95"
          >
            <LogOut size={16} className="transition-transform group-hover:-translate-x-0.5" />
            {t("common.logout")}
          </button>
        )}
      </div>
    </header>
  );
}
