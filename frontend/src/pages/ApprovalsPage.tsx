import { ApprovalCard } from "../components/approval/ApprovalCard";

export function ApprovalsPage() {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out h-full flex flex-col">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">Content Approvals</h1>
          <p className="text-sm text-zinc-500 mt-1">Review AI-generated marketing materials before publishing</p>
        </div>
      </div>
      
      <div className="flex-1 flex flex-col items-center justify-center pb-20">
        <ApprovalCard />
      </div>
    </div>
  );
}
