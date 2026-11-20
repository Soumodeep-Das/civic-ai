import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { AssessmentPanel } from "./AssessmentPanel";
afterEach(() => vi.unstubAllGlobals());
it("sends a correction and displays its saved history", async () => {
 let saved = false;
 const fetcher = vi.fn(async (_url: string, options?: RequestInit) => {
   if (options?.method === "POST") { saved = true; return { ok: true, json: async () => ({}) }; }
   if (_url.endsWith("/reviews")) return { ok: true, json: async () => saved ? [{ review_id: "r", decision: "corrected", corrected_family: "solid_waste", note: "Checked evidence" }] : [] };
   return { ok: true, json: async () => [{ assessment_id: "a", state: "suggested", suggested_family: "drainage_and_sewerage", reasons: ["experimental"] }] };
 });
 vi.stubGlobal("fetch", fetcher);
 render(<AssessmentPanel complaintId="c" csrf="test-csrf" />);
 const user = userEvent.setup();
 await user.type(await screen.findByLabelText("Review explanation"), "Checked evidence");
 await user.click(screen.getByRole("button", { name: "Save correction" }));
 await waitFor(() => expect(screen.getByText("corrected")).toBeInTheDocument());
 const post = fetcher.mock.calls.find(call => call[1]?.method === "POST");
 expect(JSON.parse(post![1]!.body as string)).toEqual({ decision: "corrected", corrected_family: "solid_waste", note: "Checked evidence" });
 expect(post![1]!.headers).toMatchObject({ "X-CSRF-Token": "test-csrf" });
});
