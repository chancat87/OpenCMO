import {
  createContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import * as authApi from "../../api/auth";
import type { AccountUsage, AuthAccount, AuthUser } from "../../types";

export interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
  user: AuthUser | null;
  account: AuthAccount | null;
  usage: AccountUsage | null;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (email: string, password: string, name?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue>({
  isAuthenticated: false,
  isLoading: true,
  isAdmin: false,
  user: null,
  account: null,
  usage: null,
  login: async () => false,
  signup: async () => false,
  logout: async () => {},
  refresh: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [account, setAccount] = useState<AuthAccount | null>(null);
  const [usage, setUsage] = useState<AccountUsage | null>(null);

  const applyPayload = useCallback((payload: authApi.AuthPayload | { authenticated: false }) => {
    if (!payload.authenticated) {
      setUser(null);
      setAccount(null);
      setUsage(null);
      return;
    }
    setUser(payload.user);
    setAccount(payload.account);
    setUsage(payload.usage);
  }, []);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      applyPayload(await authApi.getMe());
    } finally {
      setIsLoading(false);
    }
  }, [applyPayload]);

  // Listen for 401 events from apiFetch
  useEffect(() => {
    const handler = () => {
      setUser(null);
      setAccount(null);
      setUsage(null);
      queryClient.cancelQueries();
    };
    window.addEventListener("opencmo:unauthorized", handler);
    return () => window.removeEventListener("opencmo:unauthorized", handler);
  }, [queryClient]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      try {
        applyPayload(await authApi.login({ email, password }));
        await queryClient.invalidateQueries();
        return true;
      } catch {
        return false;
      }
    },
    [applyPayload, queryClient],
  );

  const signup = useCallback(
    async (email: string, password: string, name?: string) => {
      try {
        applyPayload(await authApi.signup({ email, password, name }));
        await queryClient.invalidateQueries();
        return true;
      } catch {
        return false;
      }
    },
    [applyPayload, queryClient],
  );

  const logout = useCallback(async () => {
    await authApi.logout().catch(() => undefined);
    localStorage.removeItem("opencmo_token");
    setUser(null);
    setAccount(null);
    setUsage(null);
    queryClient.clear();
  }, [queryClient]);

  const isAuthenticated = !!user;
  const isAdmin = user?.role === "admin";

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        isAdmin,
        user,
        account,
        usage,
        login,
        signup,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
