import { useState } from "react";
import { Link, useLocation } from "react-router";
import {
  LayoutDashboard,
  Radio,
  MessageSquare,
  CheckSquare,
  FolderOpen,
  Settings,
  X,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "../../api/projects";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";
import { SettingsDialog } from "../settings/SettingsDialog";

const NAV: { to: string; labelKey: TranslationKey; icon: typeof LayoutDashboard }[] = [
  { to: "/", labelKey: "nav.dashboard", icon: LayoutDashboard },
  { to: "/approvals", labelKey: "nav.approvals", icon: CheckSquare },
  { to: "/monitors", labelKey: "nav.monitors", icon: Radio },
  { to: "/chat", labelKey: "nav.aiChat", icon: MessageSquare },
];

export function Sidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { pathname } = useLocation();
  const { t } = useI18n();
  const [showSettings, setShowSettings] = useState(false);
  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  return (
    <>
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 transform flex-col bg-zinc-950/80 backdrop-blur-2xl border-r border-white/5 shadow-2xl transition-transform lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center justify-between border-b border-white/10 px-4">
          <Link to="/" className="text-lg font-bold text-zinc-100 tracking-tight" onClick={onClose}>
            OpenCMO
          </Link>
          <button className="text-zinc-400 hover:text-zinc-100 transition-colors lg:hidden" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {NAV.map(({ to, labelKey, icon: Icon }) => {
            const active = to === "/" ? pathname === to : pathname.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
                onClick={onClose}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-300 ${
                  active
                    ? "bg-indigo-500/15 text-indigo-50 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] ring-1 ring-indigo-500/30"
                    : "text-zinc-400 hover:bg-white/5 hover:text-zinc-100 hover:scale-[1.02] active:scale-[0.98]"
                }`}
              >
                <Icon size={18} className={`transition-colors ${active ? "text-indigo-400" : "text-zinc-500"}`} />
                {t(labelKey)}
              </Link>
            );
          })}
        </nav>

        {projects && projects.length > 0 && (
          <div className="border-t border-white/10 p-3">
            <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-zinc-500">
              {t("nav.projects")}
            </p>
            <div className="space-y-0.5">
              {projects.map((p) => (
                <Link
                  key={p.id}
                  to={`/projects/${p.id}`}
                  onClick={onClose}
                  className={`group flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-all duration-300 ${
                    pathname === `/projects/${p.id}`
                      ? "bg-white/10 text-zinc-100 shadow-sm"
                      : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                  }`}
                >
                  <FolderOpen size={14} className="transition-colors group-hover:text-indigo-400" />
                  <span className="truncate">{p.brand_name}</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Settings button at bottom */}
        <div className="border-t border-white/10 p-3">
          <button
            onClick={() => setShowSettings(true)}
            className="group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-zinc-400 transition-all duration-300 hover:bg-white/5 hover:text-zinc-100 hover:scale-[1.02] active:scale-[0.98]"
          >
            <Settings size={18} className="transition-transform group-hover:rotate-45" />
            {t("settings.title")}
          </button>
        </div>
      </aside>

      {showSettings && <SettingsDialog onClose={() => setShowSettings(false)} />}
    </>
  );
}
