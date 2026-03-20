const COLORS = {
  green: "bg-emerald-500/10 text-emerald-700 ring-emerald-500/20",
  blue: "bg-sky-500/10 text-sky-700 ring-sky-500/20",
  purple: "bg-violet-500/10 text-violet-700 ring-violet-500/20",
  gray: "bg-zinc-100 text-zinc-600 ring-zinc-200",
  red: "bg-rose-500/10 text-rose-700 ring-rose-500/20",
};

export function StatusBadge({
  label,
  value,
  color = "gray",
}: {
  label: string;
  value: string;
  color?: keyof typeof COLORS;
}) {
  return (
    <div className={`rounded-[1rem] p-3 text-center ring-1 ring-inset ${COLORS[color]}`}>
      <p className="text-[10px] font-semibold uppercase tracking-wider opacity-80">{label}</p>
      <p className="mt-1 text-sm font-bold tracking-tight">{value}</p>
    </div>
  );
}
