import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { PriorityPanel } from "./PriorityPanel";
afterEach(() => vi.unstubAllGlobals());
it("preserves unknown context and shows persisted deferral", async () => {
 const events: object[] = [];
 const fetcher = vi.fn(async (url: string, options?: RequestInit) => {
   if (options?.method === "POST") {
     const body = JSON.parse(options.body as string);
     if (url.endsWith("/context")) events.push({ event_id: "s", kind: "context", created_at: "2026-11-20T00:00:00Z", note: body.note, suggestion: { state: "needs_review", band: null, reasons: ["unknown_immediate_danger"], unknowns: ["immediate_danger"], emergency_review: false } });
     else events.push({ event_id: "r", kind: "review", created_at: "2026-11-20T00:01:00Z", ...body });
   }
   return { ok: true, json: async () => [...events] };
 });
 vi.stubGlobal("fetch", fetcher);
 render(<PriorityPanel complaintId="c" csrf="csrf" />);
 const user = userEvent.setup();
 await user.type(screen.getByLabelText("Context evidence explanation"), "Needs inspection");
 await user.click(screen.getByRole("button", { name: "Save context and suggest priority" }));
 await screen.findByText("Municipal review needed");
 expect(screen.getByRole("button", { name: "Accept priority" })).toBeDisabled();
 const post = fetcher.mock.calls.find(c => c[1]?.method === "POST")!;
 expect(JSON.parse(post[1]!.body as string).context.immediate_danger).toBe("unknown");
 expect(post[1]!.headers).toMatchObject({ "X-CSRF-Token": "csrf" });
 await user.type(screen.getByLabelText("Review explanation"), "Inspection requested");
 await user.click(screen.getByRole("button", { name: "Defer for review" }));
 await waitFor(() => expect(screen.getByText("Inspection requested", { selector: "p" })).toBeInTheDocument());
});
