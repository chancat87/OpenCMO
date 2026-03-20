import { useRef, useEffect, useCallback, useState, useMemo } from "react";
import ForceGraph3D from "react-force-graph-3d";
import * as THREE from "three";
import type { GraphData, GraphNode } from "../../api/graph";
import { useI18n } from "../../i18n";

/* ─── Color palette per node type ─── */
const NODE_COLORS: Record<string, number> = {
  brand: 0x6366f1,            // indigo
  keyword: 0x06b6d4,          // cyan
  discussion: 0xf59e0b,       // amber
  serp: 0x10b981,             // emerald
  competitor: 0xef4444,       // red
  competitor_keyword: 0xf97316, // orange
};

const NODE_COLORS_CSS: Record<string, string> = {
  brand: "#6366f1",
  keyword: "#06b6d4",
  discussion: "#f59e0b",
  serp: "#10b981",
  competitor: "#ef4444",
  competitor_keyword: "#f97316",
};

const LINK_COLORS: Record<string, string> = {
  has_keyword: "rgba(165, 180, 252, 0.5)",
  has_discussion: "rgba(252, 211, 77, 0.4)",
  serp_rank: "rgba(110, 231, 183, 0.4)",
  competitor_of: "rgba(252, 165, 165, 0.5)",
  comp_keyword: "rgba(253, 186, 116, 0.4)",
  keyword_overlap: "rgba(248, 113, 113, 0.7)",
};

/* ─── Node size by type ─── */
function getNodeSize(node: GraphNode): number {
  if (node.type === "brand") return 12;
  if (node.type === "competitor") return 8;
  if (node.type === "discussion") return 3 + Math.min((node.engagement ?? 0) / 30, 6);
  if (node.type === "keyword") return 5;
  if (node.type === "serp") return 4;
  return 3;
}

/* ─── Labels ─── */
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

/* ─── Create a glowing sphere with a sprite halo ─── */
function createNodeObject(node: any): THREE.Group {
  const group = new THREE.Group();
  const color = NODE_COLORS[node.type] ?? 0x94a3b8;
  const size = getNodeSize(node as GraphNode);

  // Core sphere with MeshPhong for shininess
  const geo = new THREE.SphereGeometry(size, 32, 32);
  const mat = new THREE.MeshPhongMaterial({
    color,
    emissive: color,
    emissiveIntensity: 0.3,
    shininess: 80,
    transparent: true,
    opacity: 0.92,
  });
  const sphere = new THREE.Mesh(geo, mat);
  group.add(sphere);

  // Glow halo (sprite)
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext("2d")!;
  const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  const hex = "#" + color.toString(16).padStart(6, "0");
  gradient.addColorStop(0, hex + "60");
  gradient.addColorStop(0.4, hex + "30");
  gradient.addColorStop(1, hex + "00");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 128, 128);

  const texture = new THREE.CanvasTexture(canvas);
  const spriteMat = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(spriteMat);
  sprite.scale.set(size * 5, size * 5, 1);
  group.add(sprite);

  // Brand gets a ring
  if (node.type === "brand") {
    const ringGeo = new THREE.RingGeometry(size + 2, size + 3.5, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.4,
      side: THREE.DoubleSide,
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    group.add(ring);
  }

  return group;
}

export function KnowledgeGraph({ data }: Props) {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
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

  // Auto-rotate + zoom to fit on data change
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg || data.nodes.length === 0) return;

    // Zoom to fit
    setTimeout(() => fg.zoomToFit(800, 80), 500);

    // Enable orbit auto-rotation
    const controls = fg.controls();
    if (controls) {
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.8;
    }
  }, [data]);

  // Stop rotation on interaction
  const handleNodeClick = useCallback((node: any) => {
    const fg = fgRef.current;
    if (fg) {
      const controls = fg.controls();
      if (controls) controls.autoRotate = false;
    }
    if (node.url) window.open(node.url, "_blank");
  }, []);

  // Link color
  const getLinkColor = useCallback((link: any) => {
    return LINK_COLORS[link.type] ?? "rgba(203, 213, 225, 0.3)";
  }, []);

  // Link width
  const getLinkWidth = useCallback((link: any) => {
    return link.type === "keyword_overlap" ? 2.5 : 1;
  }, []);

  // Link particles
  const getLinkParticles = useCallback((link: any) => {
    if (link.type === "keyword_overlap") return 4;
    if (link.type === "competitor_of") return 2;
    return 0;
  }, []);

  // Node label (HTML)
  const getNodeLabel = useCallback((node: any) => {
    const n = node as GraphNode;
    const typeName = typeLabels[n.type] ?? n.type;
    let html = `<div style="background:rgba(15,23,42,0.9);backdrop-filter:blur(8px);color:#fff;padding:10px 14px;border-radius:12px;font-size:12px;max-width:260px;line-height:1.5;border:1px solid rgba(99,102,241,0.3);">`;
    html += `<div style="font-size:14px;font-weight:600;margin-bottom:4px;">${n.label}</div>`;
    html += `<div style="color:#a5b4fc;font-size:11px;">${typeName}</div>`;
    if (n.platform) html += `<div style="color:#94a3b8;margin-top:3px;">${isZh ? "平台" : "Platform"}: ${n.platform}</div>`;
    if (n.engagement != null) html += `<div style="color:#94a3b8;">${isZh ? "互动分" : "Engagement"}: ${n.engagement}</div>`;
    if (n.comments != null) html += `<div style="color:#94a3b8;">${isZh ? "评论数" : "Comments"}: ${n.comments}</div>`;
    if (n.position != null) html += `<div style="color:#94a3b8;">${isZh ? "排名" : "Rank"}: #${n.position}</div>`;
    if (n.url) html += `<div style="color:#818cf8;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${n.url}</div>`;
    html += `</div>`;
    return html;
  }, [typeLabels, isZh]);

  // Label above node
  const getNodeThreeLabel = useCallback((node: any) => {
    const n = node as GraphNode;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d")!;
    const text = n.label;
    const fontSize = n.type === "brand" ? 28 : 18;
    ctx.font = `${n.type === "brand" ? "bold " : ""}${fontSize}px Inter, system-ui, sans-serif`;
    const metrics = ctx.measureText(text);
    const textWidth = metrics.width;
    canvas.width = textWidth + 20;
    canvas.height = fontSize + 12;
    ctx.font = `${n.type === "brand" ? "bold " : ""}${fontSize}px Inter, system-ui, sans-serif`;
    ctx.fillStyle = "#e2e8f0";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, canvas.width / 2, canvas.height / 2);

    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const spriteMat = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
    });
    const sprite = new THREE.Sprite(spriteMat);
    const scaleFactor = n.type === "brand" ? 1.2 : 0.8;
    sprite.scale.set(canvas.width * 0.08 * scaleFactor, canvas.height * 0.08 * scaleFactor, 1);
    sprite.position.set(0, getNodeSize(n) + 6, 0);
    return sprite;
  }, []);

  // Extend each node's 3D object to include its label
  const nodeThreeObject = useCallback((node: any) => {
    const group = createNodeObject(node);
    const label = getNodeThreeLabel(node);
    group.add(label);
    return group;
  }, [getNodeThreeLabel]);

  // Deep-copy data for force-graph (it mutates nodes)
  const graphData = useMemo(() => {
    return {
      nodes: data.nodes.map((n) => ({ ...n })),
      links: data.links.map((l) => ({ ...l })),
    };
  }, [data]);

  return (
    <div className="relative rounded-2xl border border-zinc-800/60 bg-zinc-950 shadow-xl overflow-hidden">
      {/* Legend */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap gap-2 rounded-xl bg-zinc-900/80 backdrop-blur-md px-3 py-2 shadow-lg ring-1 ring-white/5">
        {Object.entries(NODE_COLORS_CSS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full shadow-sm"
              style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}80` }}
            />
            <span className="text-[10px] font-medium text-zinc-400">
              {typeLabels[type] ?? type}
            </span>
          </div>
        ))}
      </div>

      {/* Controls hint */}
      <div className="absolute bottom-3 left-3 z-10 rounded-lg bg-zinc-900/60 px-3 py-1.5 text-[10px] text-zinc-500 backdrop-blur-sm">
        {isZh ? "🖱 拖拽旋转 · 滚轮缩放 · 点击节点打开链接" : "🖱 Drag to rotate · Scroll to zoom · Click nodes to open"}
      </div>

      {/* 3D Graph container */}
      <div ref={containerRef} style={{ width: "100%", height: 600 }}>
        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          width={dimensions.width}
          height={600}
          backgroundColor="#09090b"
          nodeThreeObject={nodeThreeObject}
          nodeLabel={getNodeLabel}
          onNodeClick={handleNodeClick}
          linkColor={getLinkColor}
          linkWidth={getLinkWidth}
          linkOpacity={0.6}
          linkDirectionalParticles={getLinkParticles}
          linkDirectionalParticleColor={getLinkColor}
          linkDirectionalParticleWidth={1.5}
          linkDirectionalParticleSpeed={0.006}
          linkCurvature={0.1}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          cooldownTicks={100}
          enableNodeDrag={true}
          enableNavigationControls={true}
          showNavInfo={false}
        />
      </div>
    </div>
  );
}
