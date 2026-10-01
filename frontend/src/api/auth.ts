import { request } from "./complaints";

export type MunicipalRole = "municipal_operator" | "municipal_admin";

export type MunicipalUser = {
  user_id: string;
  username: string;
  role: MunicipalRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
};

export type AuthSession = {
  user: MunicipalUser;
  csrf_token: string;
  expires_at: string;
};

export function login(username: string, password: string): Promise<AuthSession> {
  return request<AuthSession>("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export function getSession(): Promise<AuthSession> {
  return request<AuthSession>("/api/v1/auth/me");
}

export function logout(csrfToken: string): Promise<void> {
  return request<void>("/api/v1/auth/logout", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
  });
}

export function listUsers(): Promise<MunicipalUser[]> {
  return request<MunicipalUser[]>("/api/v1/admin/users");
}

export function createUser(
  input: { username: string; password: string; role: MunicipalRole }, csrfToken: string,
): Promise<MunicipalUser> {
  return request<MunicipalUser>("/api/v1/admin/users", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
    body: JSON.stringify(input),
  });
}

export function updateUser(
  userId: string, input: { role?: MunicipalRole; is_active?: boolean }, csrfToken: string,
): Promise<MunicipalUser> {
  return request<MunicipalUser>(`/api/v1/admin/users/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
    body: JSON.stringify(input),
  });
}
