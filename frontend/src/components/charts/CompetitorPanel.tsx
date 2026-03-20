import { useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import { useCompetitors, useAddCompetitor, useDeleteCompetitor } from "../../hooks/useGraphData";
import { useI18n } from "../../i18n";

export function CompetitorPanel({ projectId }: { projectId: number }) {
  const { data: competitors } = useCompetitors(projectId);
  const addComp = useAddCompetitor(projectId);
  const delComp = useDeleteCompetitor(projectId);
  const { locale } = useI18n();
  const isZh = locale === "zh";

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [kwInput, setKwInput] = useState("");

  const handleAdd = () => {
    if (!name.trim()) return;
    const keywords = kwInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    addComp.mutate(
      { name: name.trim(), url: url.trim() || undefined, keywords },
      {
        onSuccess: () => {
          setName("");
          setUrl("");
          setKwInput("");
          setOpen(false);
        },
      },
    );
  };

  return (
    <div className="rounded-2xl border border-zinc-200/60 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-800">
          {isZh ? "竞品管理" : "Competitors"}
        </h3>
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1 rounded-lg bg-indigo-50 px-2.5 py-1.5 text-xs font-medium text-indigo-600 ring-1 ring-inset ring-indigo-200/50 transition-all hover:bg-indigo-100 active:scale-95"
        >
          {open ? <X size={12} /> : <Plus size={12} />}
          {open ? (isZh ? "取消" : "Cancel") : (isZh ? "添加竞品" : "Add Competitor")}
        </button>
      </div>

      {/* Add form */}
      {open && (
        <div className="mb-4 space-y-2 rounded-xl bg-zinc-50/80 p-3 ring-1 ring-zinc-100 animate-in fade-in slide-in-from-top-2 duration-200">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={isZh ? "竞品名称 *" : "Competitor name *"}
            className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder={isZh ? "网址（可选）" : "URL (optional)"}
            className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <input
            value={kwInput}
            onChange={(e) => setKwInput(e.target.value)}
            placeholder={isZh ? "关键词，逗号分隔（可选）" : "Keywords, comma separated (optional)"}
            className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <button
            onClick={handleAdd}
            disabled={!name.trim() || addComp.isPending}
            className="w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition-all hover:bg-indigo-500 disabled:opacity-50 active:scale-[0.98]"
          >
            {addComp.isPending
              ? (isZh ? "添加中..." : "Adding...")
              : (isZh ? "添加" : "Add")}
          </button>
        </div>
      )}

      {/* Competitor list */}
      {!competitors?.length ? (
        <p className="text-xs text-zinc-400">
          {isZh ? "暂无竞品。添加竞品后图谱将显示竞品节点。" : "No competitors yet. Add competitors to see them in the graph."}
        </p>
      ) : (
        <div className="space-y-1.5">
          {competitors.map((c) => (
            <div
              key={c.id}
              className="flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors hover:bg-zinc-50"
            >
              <div className="min-w-0 flex-1">
                <span className="font-medium text-zinc-700">{c.name}</span>
                {c.url && (
                  <a
                    href={c.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 text-xs text-zinc-400 hover:text-indigo-500"
                  >
                    {c.url}
                  </a>
                )}
              </div>
              <button
                onClick={() => delComp.mutate(c.id)}
                className="rounded-lg p-1.5 text-zinc-300 hover:bg-rose-50 hover:text-rose-500 transition-all"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
