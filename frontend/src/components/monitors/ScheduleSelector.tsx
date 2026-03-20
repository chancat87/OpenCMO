import { useState } from "react";
import { Clock, Zap, Sun, CalendarDays, CalendarRange, Settings2 } from "lucide-react";
import { useI18n } from "../../i18n";

const PRESETS = [
  { key: "hourly",    cron: "0 * * * *",   icon: Zap,           color: "text-amber-500" },
  { key: "every6h",   cron: "0 */6 * * *", icon: Clock,         color: "text-sky-500" },
  { key: "daily",     cron: "0 9 * * *",   icon: Sun,           color: "text-indigo-500" },
  { key: "weekly",    cron: "0 9 * * 1",   icon: CalendarDays,  color: "text-violet-500" },
  { key: "monthly",   cron: "0 9 1 * *",   icon: CalendarRange, color: "text-emerald-500" },
  { key: "custom",    cron: "",             icon: Settings2,     color: "text-zinc-500" },
] as const;

export function ScheduleSelector({
  value,
  onChange,
  compact = false,
}: {
  value: string;
  onChange: (cron: string) => void;
  compact?: boolean;
}) {
  const { t } = useI18n();
  const [showCustom, setShowCustom] = useState(false);
  const [customValue, setCustomValue] = useState(value);

  const activePreset = PRESETS.find((p) => p.cron === value);
  const isCustom = !activePreset || activePreset.key === "custom";

  return (
    <div className="space-y-2">
      {!compact && (
        <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
          {t("schedule.label")}
        </label>
      )}
      <div className={`flex flex-wrap gap-1.5 ${compact ? "" : ""}`}>
        {PRESETS.map((preset) => {
          const Icon = preset.icon;
          const isActive =
            preset.key === "custom"
              ? isCustom
              : preset.cron === value;

          return (
            <button
              key={preset.key}
              type="button"
              onClick={() => {
                if (preset.key === "custom") {
                  setShowCustom(true);
                } else {
                  setShowCustom(false);
                  onChange(preset.cron);
                }
              }}
              className={`
                flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium
                transition-all duration-200 border
                ${isActive
                  ? "bg-indigo-50 border-indigo-200 text-indigo-700 shadow-sm shadow-indigo-100"
                  : "bg-white border-zinc-200/80 text-zinc-500 hover:border-zinc-300 hover:bg-zinc-50"
                }
              `}
            >
              <Icon size={12} className={isActive ? "text-indigo-500" : preset.color} />
              {t(`schedule.${preset.key}`)}
            </button>
          );
        })}
      </div>

      {/* Custom cron input */}
      {(showCustom || isCustom) && (
        <div className="flex items-center gap-2 animate-in fade-in slide-in-from-top-2 duration-200">
          <input
            type="text"
            value={customValue}
            onChange={(e) => setCustomValue(e.target.value)}
            onBlur={() => {
              if (customValue.trim()) onChange(customValue.trim());
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && customValue.trim()) {
                onChange(customValue.trim());
              }
            }}
            placeholder="0 9 * * *"
            className="w-36 rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-xs font-mono text-zinc-700 shadow-sm placeholder:text-zinc-300 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <span className="text-[10px] text-zinc-400">cron</span>
        </div>
      )}
    </div>
  );
}

/**
 * Convert a cron expression to a human-readable description.
 */
export function cronToHuman(cron: string, locale: string): string {
  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) return cron;

  const min = parts[0] ?? "0";
  const hour = parts[1] ?? "*";
  const dayOfMonth = parts[2] ?? "*";
  const dayOfWeek = parts[4] ?? "*";

  const timeStr = `${hour.padStart(2, "0")}:${min.padStart(2, "0")}`;
  const isZh = locale === "zh";

  // Every minute / every hour
  if (hour === "*" && min === "0") {
    return isZh ? "每小时" : "Every hour";
  }
  if (hour === "*" && min === "*") {
    return isZh ? "每分钟" : "Every minute";
  }

  // Every N hours
  const hourMatch = hour.match(/^\*\/(\d+)$/);
  if (hourMatch) {
    const n = hourMatch[1];
    return isZh ? `每 ${n} 小时` : `Every ${n} hours`;
  }

  // Specific day of week
  if (dayOfWeek !== "*" && dayOfMonth === "*") {
    const days = isZh
      ? ["日", "一", "二", "三", "四", "五", "六"]
      : ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const dayIdx = parseInt(dayOfWeek);
    const dayName = days[dayIdx] ?? dayOfWeek;
    return isZh ? `每周${dayName} ${timeStr}` : `${dayName} ${timeStr}`;
  }

  // Specific day of month
  if (dayOfMonth !== "*") {
    const d = parseInt(dayOfMonth);
    return isZh ? `每月 ${d} 日 ${timeStr}` : `${d}${ordinal(d)} ${timeStr}`;
  }

  // Daily at specific time
  if (hour !== "*" && dayOfWeek === "*" && dayOfMonth === "*") {
    return isZh ? `每天 ${timeStr}` : `Daily ${timeStr}`;
  }

  return cron;
}

function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0] || "th";
}
