import { useState } from "react";
import { Check, X, Sparkles, MessageSquare } from "lucide-react";

export function ApprovalCard() {
  const [direction, setDirection] = useState<"left" | "right" | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);

  // Mock data for the sprint
  const items = [
    {
      id: 1,
      platform: "Reddit",
      targetUrl: "reddit.com/r/marketing/comments/123/tools",
      content: "I've been using OpenCMO for my agency and the ROI tracking is incredible. It automatically closed the loop on our Reddit campaigns.",
      agent: "Reddit Agent",
    },
    {
      id: 2,
      platform: "X (Twitter)",
      targetUrl: "twitter.com/marketing_bro/status/456",
      content: "Stop wasting time on manual outreach. OpenCMO's AI agents just booked 3 demos for us while we were sleeping. 🚀 #SaaS #Marketing",
      agent: "Growth Agent",
    },
  ];

  const currentItem = items[currentIndex];

  const handleAction = (type: "approve" | "reject") => {
    setDirection(type === "approve" ? "right" : "left");
    setTimeout(() => {
      setDirection(null);
      setCurrentIndex((p) => p + 1);
    }, 400); // Wait for animation
  };

  if (!currentItem) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center h-[500px]">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50 text-indigo-600 ring-1 ring-indigo-200 shadow-lg mb-4">
          <Sparkles size={28} />
        </div>
        <h3 className="text-xl font-bold text-zinc-900 mb-2">You're all caught up!</h3>
        <p className="text-zinc-500">The agents are generating more content. Check back later.</p>
      </div>
    );
  }

  return (
    <div className="relative mx-auto max-w-lg w-full h-[550px] flex items-center justify-center perspective-1000">
      <div
        className={`absolute w-full rounded-[2rem] border border-zinc-200/60 bg-white ring-1 ring-zinc-950/5 shadow-2xl p-8 transition-all duration-300 ease-spring
          ${direction === "right" ? "translate-x-full rotate-12 opacity-0" : ""}
          ${direction === "left" ? "-translate-x-full -rotate-12 opacity-0" : ""}
          ${direction === null ? "scale-100 opacity-100" : "scale-95"}
        `}
      >
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-orange-50 text-orange-600 ring-1 ring-orange-200 text-xs shadow-sm">
              <MessageSquare size={16} />
            </span>
            <div>
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">{currentItem.agent}</p>
              <p className="text-sm font-bold text-zinc-900">{currentItem.platform}</p>
            </div>
          </div>
          <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-600 ring-1 ring-indigo-200">
            Pending
          </span>
        </div>

        <div className="mb-8 rounded-2xl bg-zinc-50/50 ring-1 ring-inset ring-zinc-200/50 p-6 shadow-inner">
          <p className="mb-3 text-xs font-medium text-zinc-400">TARGET URL</p>
          <a href={`https://${currentItem.targetUrl}`} target="_blank" rel="noreferrer" className="text-sm text-indigo-600 hover:underline break-all block mb-4">
            {currentItem.targetUrl}
          </a>
          <p className="text-xs font-medium text-zinc-400 mb-2">GENERATED REPLY</p>
          <p className="text-lg text-zinc-800 leading-relaxed font-medium">"{currentItem.content}"</p>
        </div>

        <div className="flex items-center justify-center gap-6">
          <button
            onClick={() => handleAction("reject")}
            className="group flex h-16 w-16 items-center justify-center rounded-full bg-white ring-1 ring-zinc-200 shadow-lg transition-all hover:scale-110 hover:bg-rose-50 hover:ring-rose-200 active:scale-95"
          >
            <X size={28} className="text-zinc-400 transition-colors group-hover:text-rose-500" />
          </button>
          <button
            onClick={() => handleAction("approve")}
            className="group flex h-16 w-16 items-center justify-center rounded-full bg-white ring-1 ring-zinc-200 shadow-lg transition-all hover:scale-110 hover:bg-emerald-50 hover:ring-emerald-200 active:scale-95"
          >
            <Check size={28} className="text-zinc-400 transition-colors group-hover:text-emerald-500" />
          </button>
        </div>
      </div>
    </div>
  );
}
