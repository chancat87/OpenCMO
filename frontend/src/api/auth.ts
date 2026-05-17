import { apiJson } from "./client";
import type { AccountUsage, AuthAccount, AuthUser } from "../types";

export interface AuthPayload {
  ok: boolean;
  authenticated: boolean;
  user: AuthUser;
  account: AuthAccount;
  is_admin: boolean;
  usage: AccountUsage;
}

export function getMe(): Promise<AuthPayload | { authenticated: false }> {
  return apiJson<AuthPayload | { authenticated: false }>("/auth/me");
}

export function signup(data: {
  email: string;
  password: string;
  name?: string;
}): Promise<AuthPayload> {
  return apiJson<AuthPayload>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function login(data: {
  email: string;
  password: string;
}): Promise<AuthPayload> {
  return apiJson<AuthPayload>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function logout(): Promise<{ ok: boolean }> {
  return apiJson<{ ok: boolean }>("/auth/logout", { method: "POST" });
}

export function getUsage(): Promise<AccountUsage> {
  return apiJson<AccountUsage>("/account/usage");
}
