import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { generateBlog, listBlogDrafts, type BlogGenerateParams } from "../api/blogGen";
import type { Locale } from "../i18n";

export function useBlogGenerate(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: BlogGenerateParams) => generateBlog(projectId, params),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project-summary", projectId] });
      qc.invalidateQueries({ queryKey: ["blog-drafts", projectId] });
    },
  });
}

export function useBlogDrafts(projectId: number, language: Locale) {
  return useQuery({
    queryKey: ["blog-drafts", projectId, language],
    queryFn: () => listBlogDrafts(projectId, language),
  });
}
