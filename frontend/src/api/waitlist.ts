import { apiJson } from "./client";

export type WaitlistSource = "home_inline" | "hosted_page";

export interface WaitlistResponse {
  ok: boolean;
  error?: string;
}

export function submitWaitlist(
  email: string,
  source: WaitlistSource,
): Promise<WaitlistResponse> {
  return apiJson<WaitlistResponse>("/waitlist", {
    method: "POST",
    body: JSON.stringify({ email, source }),
  });
}
