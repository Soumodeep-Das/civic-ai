import { Complaint, ComplaintStatus, request } from "./complaints";

export type CitizenAccount = {
  account_id: string; display_name: string; email: string;
  state: "pending_verification" | "active" | "disabled"; email_verified_at: string | null; google_connected: boolean; has_password: boolean;
};
export type CitizenSession = { account: CitizenAccount; csrf_token: string; expires_at: string };
export type CitizenHistory = { event_type: "created" | "status_changed"; previous_status: ComplaintStatus | null; new_status: ComplaintStatus; occurred_at: string };
export type OwnedComplaint = Complaint & { history: CitizenHistory[] };
export type OwnedComplaintPage = { items: OwnedComplaint[]; page: number; page_size: number; total: number; total_pages: number };

export const citizenSignup = (input: { display_name: string; email: string; password: string }) =>
  request<{ message: string }>("/api/v1/citizen-auth/sign-up", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
export const verifyCitizenEmail = (token: string) =>
  request<{ message: string }>("/api/v1/citizen-auth/verify-email", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token }) });
export const resendVerification = (email: string) =>
  request<{ message: string }>("/api/v1/citizen-auth/resend-verification", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) });
export const citizenLogin = (email: string, password: string) =>
  request<CitizenSession>("/api/v1/citizen-auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
export const getCitizenSession = () => request<CitizenSession>("/api/v1/citizen-auth/me");
export const citizenLogout = (csrf: string) => request<void>("/api/v1/citizen-auth/logout", { method: "POST", headers: { "X-CSRF-Token": csrf } });
export const forgotPassword = (email: string) => request<{ message: string }>("/api/v1/citizen-auth/forgot-password", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) });
export const resetPassword = (token: string, password: string) => request<{ message: string }>("/api/v1/citizen-auth/reset-password", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token, password }) });
export const changePassword = (current_password: string, new_password: string, csrf: string) => request<{ message: string }>("/api/v1/citizen-auth/change-password", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify({ current_password, new_password }) });
export const listMyComplaints = () => request<OwnedComplaintPage>("/api/v1/citizen/complaints");
export const getMyComplaint = (id: string) => request<OwnedComplaint>(`/api/v1/citizen/complaints/${encodeURIComponent(id)}`);
export const claimComplaint = (id: string, token: string, csrf: string) => request<OwnedComplaint>(`/api/v1/citizen/complaints/${encodeURIComponent(id)}/claim`, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify({ token }) });
