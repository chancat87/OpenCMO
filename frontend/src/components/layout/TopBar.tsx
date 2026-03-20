import { Menu, Globe, LogOut } from "lucide-react";
import { useAuth } from "../auth/useAuth";
import { useI18n } from "../../i18n";

export function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { isAuthenticated, logout } = useAuth();
  const { locale, setLocale, t } = useI18n();

  return (
    <header className="flex h-16 items-center justify-between border-b border-zinc-200/50 bg-white/60 px-4 backdrop-blur-xl supports-[backdrop-filter]:bg-white/40 transition-colors duration-500">
      <button className="rounded-xl p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 transition-all hover:scale-105 active:scale-95 lg:hidden" onClick={onMenuClick}>
        <Menu size={20} />
      </button>
      <div className="flex-1" />
      <div className="flex items-center gap-3 pr-2 lg:pr-4">
        <button
          onClick={() => setLocale(locale === "en" ? "zh" : "en")}
          className="group flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-medium text-zinc-500 transition-all duration-300 hover:bg-zinc-100 hover:text-zinc-900 hover:scale-105 active:scale-95"
        >
          <Globe size={16} className="transition-transform group-hover:rotate-12" />
          {locale === "en" ? "中文" : "EN"}
        </button>
        {isAuthenticated && (
          <button
            onClick={logout}
            className="group flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-medium text-zinc-500 transition-all duration-300 hover:bg-zinc-100 hover:text-zinc-900 hover:scale-105 active:scale-95"
          >
            <LogOut size={16} className="transition-transform group-hover:-translate-x-0.5" />
            {t("common.logout")}
          </button>
        )}
      </div>
    </header>
  );
}
