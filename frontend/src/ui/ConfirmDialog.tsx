import { KeyboardEvent, ReactNode, RefObject, useEffect, useRef } from "react";

type Props = { open: boolean; title: string; description: ReactNode; confirmLabel: string; busy?: boolean; destructive?: boolean; returnFocusRef?: RefObject<HTMLElement | null>; onCancel: () => void; onConfirm: () => void };

export function ConfirmDialog({ open, title, description, confirmLabel, busy = false, destructive = false, returnFocusRef, onCancel, onConfirm }: Props) {
  const dialog = useRef<HTMLDivElement>(null); const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => { if (!open) return; cancel.current?.focus(); return () => returnFocusRef?.current?.focus(); }, [open, returnFocusRef]);
  if (!open) return null;
  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape" && !busy) { event.preventDefault(); onCancel(); return; }
    if (event.key !== "Tab") return;
    const controls = Array.from(dialog.current?.querySelectorAll<HTMLElement>('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])') ?? []);
    if (!controls.length) return; const first = controls[0]; const last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
  return <div className="dialog-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) onCancel(); }}><div ref={dialog} className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title" aria-describedby="confirm-description" onKeyDown={handleKeyDown}><h2 id="confirm-title">{title}</h2><div id="confirm-description">{description}</div><div className="dialog-actions"><button ref={cancel} type="button" className="secondary-button" disabled={busy} onClick={onCancel}>Cancel</button><button type="button" className={destructive ? "danger-button" : "primary-action"} disabled={busy} onClick={onConfirm}>{busy ? "Working…" : confirmLabel}</button></div></div></div>;
}
