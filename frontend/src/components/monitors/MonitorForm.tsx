import { useState } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import { useI18n } from "../../i18n";
import { ScheduleSelector } from "./ScheduleSelector";

export function MonitorForm({
  onSubmit,
  isLoading,
}: {
  onSubmit: (data: { url: string; cron_expr: string }) => Promise<void>;
  isLoading: boolean;
}) {
  const { t } = useI18n();
  const [url, setUrl] = useState("");
  const [cronExpr, setCronExpr] = useState("0 9 * * *");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    await onSubmit({ url: url.trim(), cron_expr: cronExpr });
    setUrl("");
  };

  return (
    <div className="rounded-2xl border border-zinc-200/60 bg-gradient-to-br from-white to-indigo-50/30 p-6 shadow-sm ring-1 ring-zinc-950/5">
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-100 ring-1 ring-indigo-200/50">
          <Sparkles size={16} className="text-indigo-600" />
        </div>
        <p className="text-sm text-zinc-500">{t("monitorForm.subtitle")}</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-3">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            type="url"
            required
            placeholder={t("monitorForm.urlPlaceholder")}
            className="flex-1 rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm shadow-sm transition-shadow placeholder:text-zinc-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-500 hover:shadow-md disabled:opacity-50 active:scale-95"
          >
            {isLoading ? (
              t("monitorForm.analyzing")
            ) : (
              <>
                {t("monitorForm.startMonitoring")}
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
        <ScheduleSelector value={cronExpr} onChange={setCronExpr} />
      </form>
    </div>
  );
}
