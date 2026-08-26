# Otherwhere Capital Design System

## Company & Product Context

**Otherwhere Capital** is a financial research and analysis firm. This design system documents the visual language and UI components from their flagship analytical product: the **SPCX Valuation App** — an interactive sum-of-the-parts discounted cash flow model for SpaceX (ticker: SPCX), built around the company's 2025 IPO.

The app lets analysts drag ~68 sliders across four business segments (Space, Connectivity, AI, Expansion) and see the resulting per-share intrinsic value update live. It is a professional-grade financial tool, not a consumer product: dense information, precision typography, and editorial restraint define its aesthetic.

### Author
The app was designed and authored by **Dan McSpirit** ([linkedin.com/in/danmcspirit](https://www.linkedin.com/in/danmcspirit)). The system codifies the visual decisions embedded in that work.

### Sources Used
- **Codebase**: `spcx-valuation-app/` (mounted via File System Access API)
  - `src/App.jsx` — full application layout and component wiring
  - `src/App.css` — all design tokens and component styles
  - `src/index.css` — body/root reset
  - `src/components/` — SliderControl, SegmentChart, HeadlineValuation, SliderPanel
  - `cursor_implementation_brief.md` — product spec and model methodology
- **No Figma file was provided.** Visual ground truth is the codebase CSS.

---

## Content Fundamentals

### Voice & Tone
- **Precise and declarative.** Sentences make a claim and stop. No hedging with "may" or "might" when a number is knowable.
- **Technical, not jargon-heavy.** The audience is financially literate. Terms like WACC, EBIT, and H-model appear without definition, but novel model choices are always explained in plain language.
- **First person is absent.** Copy never says "I" or "we." It says "the model," "this segment," "the calculation."
- **No emoji.** Ever.
- **Not investment advice** appears as a footnote in every surface that shows a per-share price. This is a legal necessity, not boilerplate.
- **All caps used structurally**, never decoratively — section labels, column headers, ticker marks only.
- **Numbers are the primary content.** Text is scaffolding for numbers. Labels are as short as possible.

### Casing patterns
| Use | Case |
|---|---|
| Section labels | ALL CAPS, tracked |
| Column headers | ALL CAPS, tracked |
| Body / explanation copy | Sentence case |
| Navbar brand subtitle | ALL CAPS |
| Footer notices | ALL CAPS |
| Slider labels | Title Case or sentence case |

### Specific copy examples
- `Equity Value · Per Share · Rounded to Nearest USD` — dots as separators, spaced
- `Not investment advice` — lowercase, subdued
- `Model defaults are starting values only · All figures USD million unless noted`
- `Reset to model defaults` — action label, lowercase
- Segment descriptions are dense paragraphs (~60 words), no bullet points

---

## Visual Foundations

### Color
- **Primary palette**: Deep navy (#002 equivalent in oklch), used at three lightnesses: full navy for headings and key figures, mid-navy for body text, light-navy for labels and muted copy.
- **Gold accent** (`oklch(0.76 0.13 82)`): The single accent color. Used for the 3px topbar stripe, all slider thumbs, chart lines for margin, and any interactive affordance that needs attention. Warm amber-gold, never yellow.
- **White background**: The page is always white. No dark mode exists in the source.
- **Subtle surface** (`oklch(0.975 0.006 258)`): A near-imperceptible blue-white used to highlight total/summary rows. Not a card background — a zebra-stripe equivalent.
- **Gold wash** (`oklch(0.96 0.018 82)`): Reserved for optional accent backgrounds.
- **Status**: Green for positive spread/value, red-orange for negative enterprise value warnings.
- **No gradients.** No shadows. No blurs.

### Typography
Three-font system with strict role separation:
- **Playfair Display (serif)**: Hero numbers (per-share price), section titles like "Model Methodology & Mechanics". Used only where scale and weight need editorial authority. Always set large.
- **IBM Plex Sans (sans)**: All body copy, slider labels, table cell labels, footnotes, paragraph text. Workhorse of the UI.
- **IBM Plex Mono (mono)**: Every number, every ticker/code, every section label in ALL CAPS, every button. Mono ensures tabular number alignment and signals "data."

### Layout
- Max-width 1600px, centered.
- 40px horizontal gutters throughout (20px on mobile).
- Strict horizontal division into sections separated by 1px `--border` lines.
- Within sections, columns are separated by 1px vertical borders.
- No cards with shadows. Information is organized by border lines, not floating panels.
- Grid layouts: 4-column for segment analysis and output tables; flex for nav.

### Topbar
A 3px gold stripe sits above the navbar. It is the first element in the DOM, the first visual signal of the brand.

### Borders & Radius
- Borders everywhere: section dividers, column separators, table row lines, input outlines.
- **Border radius is effectively zero** for all structural elements. The only exception is the 1px border-radius on the range track and 50% on the slider thumb.
- No card shadows. Elevation is communicated only through background color change (e.g., `--bg-subtle` rows).

### Interactive States
- **Slider thumb**: Gold circle, 10×10px. No transition on value.
- **Buttons**: `border: 1px solid var(--border-mid)`. On hover, `color: var(--navy)` and `border-color: var(--navy-mid)`. Transition 150ms ease.
- **Links**: Underlined via `border-bottom: 1px solid`. Not text-decoration.
- **No press/scale animations.** No bounces.

### Animation & Motion
- `transition: color 0.15s, border-color 0.15s` on buttons only.
- Chart lines use `isAnimationActive={false}` — even recharts animations are disabled.
- No entrance animations, no loading spinners, no page transitions.
- The aesthetic is **static precision**, not kinetic UI.

### Spacing System
Multiples of 2px at the small end; 4px, 8px, 16px, 20px, 28px, 32px, 40px at layout scale. 40px is the canonical gutter.

### Imagery
No photography. No illustrations. No SVG decorative elements. The only "imagery" is charts (recharts line charts) rendered with navy and gold lines on a white background.

### Charts
- recharts `<LineChart>` — two axes (primary metric left, operating margin % right).
- Navy line for primary metric (e.g., Launches, Subscribers, Megawatts).
- Gold line for margin.
- Minimal axes: only start and end year tick marks shown.
- No grid. White background. 1px `--border` chart border.
- Custom legend: small 8×8px colored squares, centered below chart.

---

## Iconography

**No icon system is used in the source codebase.** There are no SVG icons, no icon font, no emoji, no unicode glyph stand-ins.

The only "icon-like" element is the `↗` external link indicator on the Dan McSpirit LinkedIn link, rendered as the HTML entity `&#8599;` (↗).

### Intentional absence
The design deliberately avoids iconography. Every label is text. Navigation has no hamburger, no chevron, no search icon. Actions are text buttons. This is consistent with the financial-editorial aesthetic: no chrome, no decoration.

If icons become necessary in future surfaces, the recommended approach would be a stroke-weight icon set (e.g., Lucide) at 14–16px, in `var(--navy-light)`, never filled.

---

## File Index

```
styles.css                    → Global CSS entry point (@import only)
readme.md                     → This file
SKILL.md                      → Agent skill definition

tokens/
  fonts.css                   → Google Fonts @import (FLAG: self-host for production)
  colors.css                  → All color custom properties + semantic aliases
  typography.css              → Font families, scale, weight, tracking
  spacing.css                 → Space scale, layout constants, radii
  forms.css                   → Body reset, range slider cross-browser styles, link defaults

guidelines/
  colors-navy.card.html       → Navy scale specimens
  colors-gold-semantic.card.html → Gold + status color specimens
  colors-surfaces.card.html   → Surfaces + border specimens
  type-display.card.html      → Playfair Display specimens
  type-sans.card.html         → IBM Plex Sans specimens
  type-mono.card.html         → IBM Plex Mono specimens
  type-scale.card.html        → Full type scale reference
  spacing.card.html           → Spacing token reference
  brand.card.html             → Brand mark + topbar treatment

components/
  controls/
    SliderControl.jsx/.d.ts   → Range slider with label + live value
    GridCell.jsx/.d.ts        → Compact grid cell (interactive or static)
    controls.card.html        → Component specimens
  data/
    BridgeRow.jsx/.d.ts       → Financial summary row
    data.card.html            → Component specimens
  navigation/
    NavBar.jsx/.d.ts          → Top navigation bar
    navigation.card.html      → Component specimens

ui_kits/
  valuation_app/
    index.html                → Full SPCX Valuation App recreation

assets/
  (no logo provided — see note below)
```

### Logo note
No logo file was provided. The brand mark in the app is the ticker **SPCX** rendered in IBM Plex Mono, 13px, weight 500, letter-spacing 0.14em, color `var(--navy)`. This typographic mark is the de-facto identity. If a proper mark exists, drop it into `assets/` and update the NavBar component.

---

## Intentional Additions

None. Every component in this system corresponds directly to a component or repeated pattern in the source codebase. No standard primitives (Toast, Avatar, Tabs, etc.) were invented.

---

## Caveats

- **Fonts**: Google Fonts CDN. Self-host for production.
- **No logo file**: Brand mark is type-only.
- **SegmentChart** (recharts): Not a standalone component in this design system — it depends on the recharts library. The chart visual language is documented in Visual Foundations.
- **Calculation engine** (`operating_engine.mjs`): Not included in the design system. The UI kit uses static representative values.
