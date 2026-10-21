import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiRequest } from "../api/client";
import type { TokenResponse, User } from "../types";

interface AuthState {
  user: User | null;
  ready: boolean;
  login: (username: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);
const STORAGE_KEY = "ei_access_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  // On page load, check whether a saved token is still valid.
  useEffect(() => {
    const savedToken = sessionStorage.getItem(STORAGE_KEY);
    if (!savedToken) {
      setReady(true);
      return;
    }
    apiRequest<User>("/auth/me", { token: savedToken })
      .then(setUser)
      .catch(() => sessionStorage.removeItem(STORAGE_KEY))
      .finally(() => setReady(true));
  }, []);

  async function login(username: string, password: string): Promise<User> {
    const tokens = await apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: { username, password },
    });
    const me = await apiRequest<User>("/auth/me", { token: tokens.access_token });
    sessionStorage.setItem(STORAGE_KEY, tokens.access_token);
    setUser(me);
    return me;
  }

  function logout() {
    sessionStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, ready, login, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}