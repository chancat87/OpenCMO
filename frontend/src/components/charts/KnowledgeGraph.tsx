import { useRef, useEffect, useCallback, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import type { GraphData, GraphNode } from "../../api/graph";
import { useI18n } from "../../i18n";

/* ─── Color palette per node type ─── */
const NODE_COLORS: Record<string, string> = {
  brand: "#6366f1",            // indigo
  keyword: "#06b6d4",          // cyan
  discussion: "#f59e0b",       // amber
  serp: "#10b981",             // emerald
  competitor: "#ef4444",       // red
  competitor_keyword: "#f97316", // orange
};

const LINK_COLORS: Record<string, string> = {
  has_keyword: "#a5b4fc",      // indigo-300
  has_discussion: "#fcd34d",   // amber-300
  serp_rank: "#6ee7b7",        // emerald-300
  competitor_of: "#fca5a5",    // red-300
  comp_keyword: "#fdba74",     // orange-300
  keyword_overlap: "#f87171",  // red-400 dashed
};

/* ─── Node size by type ─── */
function getNodeSize(node: GraphNode): number {
  if (node.type === "brand") return 20;
  if (node.type === "competitor") return 12;
  if (node.type === "discussion") return 6 + Math.min((node.engagement ?? 0) / 20, 10);
  if (node.type === "keyword") return 8;
  if (node.type === "serp") return 6;
  return 5;
}

/* ─── Label for type (used in legend) ─── */
const TYPE_LABELS_EN: Record<string, string> = {
  brand: "Brand",
  keyword: "Keyword",
  discussion: "Discussion",
  serp: "SERP Rank",
  competitor: "Competitor",
  competitor_keyword: "Competitor KW",
};

const TYPE_LABELS_ZH: Record<string, string> = {
  brand: "品牌",
  keyword: "关键词",
  discussion: "社区讨论",
  serp: "搜索排名",
  competitor: "竞品",
  competitor_keyword: "竞品关键词",
};

interface Props {
  data: GraphData;
}

export function KnowledgeGraph({ data }: Props) {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const { locale } = useI18n();
  const isZh = locale === "zh";
  const typeLabels = isZh ? TYPE_LABELS_ZH : TYPE_LABELS_EN;

  // Measure container
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0]!.contentRect;
      if (width > 0 && height > 0) setDimensions({ width, height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Zoom to fit on data change
  useEffect(() => {
    const fg = fgRef.current;
    if (fg && data.nodes.length > 0) {
      setTimeout(() => fg.zoomToFit(400, 60), 500);
    }
  }, [data]);

  const handleNodeClick = useCallback((node: any) => {
    if (node.url) window.open(node.url, "_blank");
  }, []);

  const paintNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const r = getNodeSize(node as GraphNode);
    const color = NODE_COLORS[node.type] ?? "#94a3b8";

    // Glow for hovered
    if (hoveredNode?.id === node.id) {
      ctx.shadowColor = color;
      ctx.shadowBlur = 20;
    }

    // Circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    // Brand: double ring
    if (node.type === "brand") {
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 3;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + 3, 0, 2 * Math.PI);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Keyword overlap highlight (pulsing ring handled via CSS animation emulation)
    if (node.type === "competitor_keyword") {
      ctx.strokeStyle = "#f87171";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    ctx.shadowColor = "transparent";
    ctx.shadowBlur = 0;

    // Label
    const fontSize = Math.max(10 / globalScale, 3);
    ctx.font = `${node.type === "brand" ? "bold " : ""}${fontSize}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = "#1e293b";
    ctx.fillText(node.label, node.x, node.y + r + 2);
  }, [hoveredNode]);

  const paintLink = useCallback((link: any, ctx: CanvasRenderingContext2D) => {
    const color = LINK_COLORS[link.type] ?? "#cbd5e1";
    ctx.strokeStyle = color;
    ctx.lineWidth = link.type === "keyword_overlap" ? 2 : 1;

    // Dashed for overlap
    if (link.type === "keyword_overlap") {
      ctx.setLineDash([4, 4]);
    } else {
      ctx.setLineDash([]);
    }

    ctx.beginPath();
    ctx.moveTo(link.source.x, link.source.y);
    ctx.lineTo(link.target.x, link.target.y);
    ctx.stroke();
    ctx.setLineDash([]);
  }, []);

  return (
    <div className="relative rounded-2xl border border-zinc-200/60 bg-white shadow-sm overflow-hidden">
      {/* Legend */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap gap-2 rounded-xl bg-white/90 backdrop-blur-sm px-3 py-2 shadow-sm ring-1 ring-zinc-200/50">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-[10px] font-medium text-zinc-500">
              {typeLabels[type] ?? type}
            </span>
          </div>
        ))}
      </div>

      {/* Hover tooltip */}
      {hoveredNode && (
        <div className="absolute top-3 right-3 z-10 max-w-xs rounded-xl bg-zinc-900/90 px-4 py-3 text-xs text-white shadow-lg backdrop-blur-sm">
          <p className="font-semibold text-sm mb-1">{hoveredNode.label}</p>
          <p className="text-zinc-300 capitalize">{typeLabels[hoveredNode.type] ?? hoveredNode.type}</p>
          {hoveredNode.platform && <p className="text-zinc-400 mt-0.5">{isZh ? "平台" : "Platform"}: {hoveredNode.platform}</p>}
          {hoveredNode.engagement != null && <p className="text-zinc-400">{isZh ? "互动分" : "Engagement"}: {hoveredNode.engagement}</p>}
          {hoveredNode.comments != null && <p className="text-zinc-400">{isZh ? "评论数" : "Comments"}: {hoveredNode.comments}</p>}
          {hoveredNode.position != null && <p className="text-zinc-400">{isZh ? "排名" : "Rank"}: #{hoveredNode.position}</p>}
          {hoveredNode.url && <p className="text-indigo-300 mt-1 truncate">{hoveredNode.url}</p>}
        </div>
      )}

      {/* Graph container */}
      <div ref={containerRef} style={{ width: "100%", height: 520 }}>
        <ForceGraph2D
          ref={fgRef}
          graphData={data}
          width={dimensions.width}
          height={dimensions.height}
          nodeCanvasObject={paintNode}
          linkCanvasObject={paintLink}
          onNodeClick={handleNodeClick}
          onNodeHover={(node: any) => setHoveredNode(node as GraphNode | null)}
          nodeLabel={() => ""}
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          backgroundColor="transparent"
        />
      </div>
    </div>
  );
}
