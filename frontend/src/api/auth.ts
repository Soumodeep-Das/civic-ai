import { request } from "./complaints";

export type MunicipalRole = "municipal_operator" | "municipal_admin";

export type MunicipalUser = {
  user_id: string;
  username: string;
  email: string | null;
  display_name: string | null;
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

export type DepartmentMember = Pick<MunicipalUser, "user_id" | "username" | "role" | "is_active">;
export type MunicipalDepartment = {
  department_id: string; slug: string; display_name: string; description: string | null;
  is_active: boolean; created_at: string; updated_at: string; members: DepartmentMember[];
};
export type StaffInvitation = {
  invitation_id: string; email: string; role: MunicipalRole; department_ids: string[];
  expires_at: string; accepted_at: string | null; revoked_at: string | null; created_at: string;
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

export function listDepartments(includeInactive = true): Promise<MunicipalDepartment[]> {
  return request(`/api/v1/admin/departments?include_inactive=${includeInactive}`);
}

export function createDepartment(input: { slug: string; display_name: string; description?: string }, csrfToken: string): Promise<MunicipalDepartment> {
  return request("/api/v1/admin/departments", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify(input) });
}

export function updateDepartment(departmentId: string, input: { display_name?: string; description?: string; is_active?: boolean }, csrfToken: string): Promise<MunicipalDepartment> {
  return request(`/api/v1/admin/departments/${encodeURIComponent(departmentId)}`, { method: "PATCH", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify(input) });
}

export function addDepartmentMember(departmentId: string, userId: string, csrfToken: string): Promise<DepartmentMember> {
  return request(`/api/v1/admin/departments/${encodeURIComponent(departmentId)}/members`, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify({ user_id: userId }) });
}

export function removeDepartmentMember(departmentId: string, userId: string, csrfToken: string): Promise<void> {
  return request(`/api/v1/admin/departments/${encodeURIComponent(departmentId)}/members/${encodeURIComponent(userId)}`, { method: "DELETE", headers: { "X-CSRF-Token": csrfToken } });
}

export function listStaffInvitations(): Promise<StaffInvitation[]> {
  return request("/api/v1/admin/staff-invitations");
}

export function inviteStaff(input: { email: string; role: MunicipalRole; department_ids: string[] }, csrfToken: string): Promise<StaffInvitation> {
  return request("/api/v1/admin/staff-invitations", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify(input) });
}

export function revokeStaffInvitation(id: string, csrfToken: string): Promise<StaffInvitation> {
  return request(`/api/v1/admin/staff-invitations/${encodeURIComponent(id)}/revoke`, { method: "POST", headers: { "X-CSRF-Token": csrfToken } });
}

export function acceptStaffInvitation(input: { token: string; display_name: string; username: string; password: string }): Promise<{ message: string; username: string }> {
  return request("/api/v1/staff/accept-invite", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
}
