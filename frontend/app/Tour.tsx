// Self-contained guided tour. Highlights one element at a time via a CSS spotlight
// (huge box-shadow on the cutout) and shows a positioned popup with Next/Back/Skip.
// Per-page tours fire after every login (sessionStorage flag, cleared on login/logout).
"use client";

import { useEffect, useState } from "react";

export interface TourStep {
  // CSS id of the element to highlight; if missing on the page, the step is skipped
  id: string;
  title: string;
  body: string;
}

interface TourProps {
  steps: TourStep[];
  // Per-page sessionStorage key (e.g. "tour_main_seen") — set on dismiss/complete
  storageKey: string;
}

/** One-time guided tour. Renders nothing if the storageKey flag is already set. */
export function Tour({ steps, storageKey }: TourProps) {
  // -1 = inactive (closed or not yet started); 0..N-1 = current step
  const [idx, setIdx] = useState<number>(-1);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [vp, setVp] = useState<{ w: number; h: number }>({ w: 1024, h: 768 });

  // Decide whether to start the tour on mount. Brief delay lets the page settle
  // (server-render hydration, conditional sections, etc.) before measuring.
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem(storageKey) === "1") return;
    setVp({ w: window.innerWidth, h: window.innerHeight });
    const t = setTimeout(() => setIdx(0), 250);
    return () => clearTimeout(t);
  }, [storageKey]);

  // Locate + measure the current step's target. Re-fires when idx or the steps array changes.
  useEffect(() => {
    if (idx < 0 || idx >= steps.length) return;
    let cancelled = false;
    const target = steps[idx].id;
    const find = () => {
      if (cancelled) return;
      const el = document.getElementById(target);
      if (!el) {
        // Step's target isn't on this page — auto-skip to the next step (or close at end)
        if (idx + 1 < steps.length) setIdx((i) => i + 1);
        else dismiss();
        return;
      }
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      // Wait for scroll-smooth to settle before snapshotting the rect
      setTimeout(() => { if (!cancelled) setRect(el.getBoundingClientRect()); }, 360);
    };
    find();

    const onResize = () => {
      const el = document.getElementById(target);
      if (el) setRect(el.getBoundingClientRect());
      setVp({ w: window.innerWidth, h: window.innerHeight });
    };
    window.addEventListener("resize", onResize);
    window.addEventListener("scroll", onResize, true);
    return () => {
      cancelled = true;
      window.removeEventListener("resize", onResize);
      window.removeEventListener("scroll", onResize, true);
    };
    // dismiss is stable; intentionally not in deps to avoid re-running effect on identity change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx, steps]);

  const dismiss = () => {
    if (typeof window !== "undefined") sessionStorage.setItem(storageKey, "1");
    setIdx(-1);
    setRect(null);
  };

  if (idx < 0 || idx >= steps.length || !rect) return null;

  const step = steps[idx];

  // Popup placement: below the highlighted element if there's vertical room, else above.
  // Horizontally clamp so the 320px-wide popup never overflows the viewport.
  const POPUP_W = 340;
  const placeBelow = rect.bottom + 220 < vp.h;
  const top = placeBelow ? rect.bottom + window.scrollY + 14 : rect.top + window.scrollY - 14;
  const left = Math.min(
    Math.max(12, rect.left + window.scrollX),
    Math.max(12, window.scrollX + vp.w - POPUP_W - 12),
  );

  return (
    <>
      {/* Spotlight cutout: a transparent box surrounded by a huge translucent box-shadow.
          Clicking the dim region dismisses the tour (matching common UX). */}
      <div
        className="tour-spotlight"
        style={{
          top: rect.top + window.scrollY - 6,
          left: rect.left + window.scrollX - 6,
          width: rect.width + 12,
          height: rect.height + 12,
        }}
        onClick={dismiss}
      />
      <div
        className={`tour-popup ${placeBelow ? "tour-popup-below" : "tour-popup-above"}`}
        style={{ top, left, width: POPUP_W }}
      >
        <div className="tour-popup-step">Step {idx + 1} of {steps.length}</div>
        <div className="tour-popup-title">{step.title}</div>
        <div className="tour-popup-body">{step.body}</div>
        <div className="tour-popup-controls">
          <button onClick={dismiss} className="tour-skip">Skip tour</button>
          <span style={{ flex: 1 }} />
          {idx > 0 && (
            <button className="tour-back" onClick={() => setIdx((i) => i - 1)}>← Back</button>
          )}
          {idx < steps.length - 1 ? (
            <button className="tour-next" onClick={() => setIdx((i) => i + 1)}>Next →</button>
          ) : (
            <button className="tour-next" onClick={dismiss}>Got it ✓</button>
          )}
        </div>
      </div>
    </>
  );
}

/** Clears every `tour_*` sessionStorage flag so all per-page tours fire on the next visit.
 * Called from handleLogin (success) and handleLogout on the main page. */
export function resetTourFlags(): void {
  if (typeof window === "undefined") return;
  const keys: string[] = [];
  for (let i = 0; i < sessionStorage.length; i++) {
    const k = sessionStorage.key(i);
    if (k && k.startsWith("tour_")) keys.push(k);
  }
  for (const k of keys) sessionStorage.removeItem(k);
}
