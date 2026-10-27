# OpenSpec Change Proposal: Monochrome High-Craft & Fully Responsive UI Redesign

**Change Name:** `monochrome-responsive-redesign`  
**Status:** PROPOSED  
**Author:** Antigravity Pair Programming Session  
**Target Capability:** `dashboard-ui`  
**Date:** 2026-10-27  

---

## 1. Problem Statement
User testing and critique of the previous UI revealed three critical issues:
1. **Garish Colors ("Crap" Colors):** Yellow fonts (amber text in carbs/metrics), red fonts (rose text in HR), and extensive purple shades (purple buttons, purple slider thumbs, purple gradient logo, purple active tabs) distract clinicians and degrade the high-craft clinical feel.
2. **Missing Screen Responsive Layout:** On viewports under 1440px or smaller laptop screens, the dual-rail layout (56px micro-rail + 240px fixed sidebar) cramps the main chart canvas and causes horizontal scrolling and layout breakage.
3. **Dark Mode Default:** The user strongly dislikes dark mode as the default and requested the clean white/grey layout with black/white font effects.

---

## 2. Proposed Changes

### A. Pure Monochrome / Neutral High-Craft Design System
- **Default Theme:** Light mode by default (`<html>` without `dark` class, default theme `'light'`).
- **Color Palette:**
  - Canvas: `#f8fafc` / `#f1f5f9` (clean background grey).
  - Cards: `#ffffff` with 1px border `#e2e8f0` and soft elevation.
  - Primary Text: `#0f172a` (rich deep black/slate).
  - Secondary Text: `#475569` (slate 600).
  - Accent / Primary CTA: Solid black `#0f172a` with white text.
  - Active Tab Indicator: 2px solid black underline (`#0f172a`).
  - Logo: Replace garish purple gradient "AE" logo with a minimalist geometric monochrome clinical glyph in crisp black & white.
  - Range Sliders: Clean black thumb `#0f172a` on neutral track `#e2e8f0`.
  - Chart Colors: Restrained high-contrast palette (precision charcoal prediction curve `#0f172a` with subtle green accent `#059669`, dashed ground truth `#64748b`, subtle target corridor).
  - Purge all yellow and red fonts across metric cards, badges, and controls.

### B. Fully Responsive Dual-Rail & Grid Layout
- **Breakpoints:**
  - `xl` ($\ge 1280\text{px}$): Full dual-rail (56px micro-rail + 240px sidebar + flex canvas).
  - `lg` ($1024\text{px} - 1279\text{px}$): Sidebar auto-collapses to give full width to the chart and tables, with toggle icon.
  - `sm`/`md` ($< 1024\text{px}$): Sidebar becomes a slide-out drawer or clean top navigation.
- **Bento KPI Grid:** `grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3.5`.
- **Canvas & Tables:** `min-w-0 flex-1 overflow-x-auto` to prevent horizontal viewport clipping.

---

## 3. Scope & Verification
- Modify `services/backend/static/index.html` (primary dashboard).
- Modify `services/frontend/src/app/page.tsx` and `globals.css` (Next.js dashboard).
- Maintain 100% contract compatibility across `/health`, `/patients`, `/predict`, `/simulate`, `/meal-presets`, and `/ws/replay/*`.
- Verify with `pytest tests/test_services.py` and `ruff check`.
