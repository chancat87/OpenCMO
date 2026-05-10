import { apiJson } from "./client";
import type { Locale } from "../i18n";
import type { BlogDraft, BlogStyle, MarketingSkillId } from "../types";

export interface BlogGenerateParams {
  style: BlogStyle;
  skill_id: MarketingSkillId;
  bilingual: boolean;
  language: Locale;
}

export interface BlogGenerateResult {
  task_id: string;
  project_id: number;
  style: string;
  language?: string | null;
  skill_id: MarketingSkillId;
  skill_name: string;
  status: string;
}

export function generateBlog(
  projectId: number,
  params: BlogGenerateParams,
): Promise<BlogGenerateResult> {
  return apiJson<BlogGenerateResult>(`/projects/${projectId}/blog/generate`, {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function listBlogDrafts(projectId: number, language: Locale): Promise<BlogDraft[]> {
  return apiJson<BlogDraft[]>(`/projects/${projectId}/blog/drafts?language=${encodeURIComponent(language)}`);
}

export function getBlogDraft(draftId: number): Promise<BlogDraft> {
  return apiJson<BlogDraft>(`/blog/drafts/${draftId}`);
}
