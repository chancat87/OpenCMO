import { ExternalLink } from "lucide-react";
import type { Project } from "../../types";

export function ProjectHeader({ project }: { project: Project }) {
  return (
    <div className="mb-8 border-b border-zinc-200/50 pb-6 flex items-start justify-between">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900">{project.brand_name}</h1>
          <span className="rounded-md bg-zinc-100/80 ring-1 ring-zinc-200/50 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
            {project.category}
          </span>
        </div>
        <a
          href={project.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-500 transition-colors"
        >
          {project.url} <ExternalLink size={14} />
        </a>
      </div>
    </div>
  );
}
