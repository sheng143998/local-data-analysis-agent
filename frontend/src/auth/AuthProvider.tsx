import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { ApiError } from '../api/client';
import * as authClient from '../api/authClient';
import type { AuthUser } from '../types/auth';

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (displayName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authClient.getCurrentUser().then((response) => setUser(response.user)).catch(() => setUser(null)).finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authClient.login({ email, password });
    setUser(response.user);
  }, []);
  const register = useCallback(async (displayName: string, email: string, password: string) => {
    const response = await authClient.register({ display_name: displayName, email, password });
    setUser(response.user);
  }, []);
  const logout = useCallback(async () => {
    try {
      await authClient.logout();
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) throw error;
    } finally {
      setUser(null);
    }
  }, []);

  return <AuthContext.Provider value={useMemo(() => ({ user, loading, login, register, logout }), [user, loading, login, register, logout])}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('AuthProvider is required');
  return value;
}
