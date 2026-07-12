export type UserRole = 'analyst' | 'admin';

export type AuthUser = {
  id: string;
  email: string;
  display_name: string;
  role: UserRole;
  created_at: string;
};

export type AuthResponse = {
  user: AuthUser;
  csrf_token: string;
};
