# Horus Analytics II: Design System

## 1. Vision
A cold, military-grade financial terminal designed for quantitative operators. It is an "eye of the storm" for navigating volatile markets with mechanical detachment and supreme clarity.

## 2. Color Palette
- **Background**: Slate 950 (Jet Black/Deep Gray)
- **Primary Support**: Cyan/Teal (HEX: #25d1f4) - Used for accumulation, stability, and supportive signals.
- **Alert/Conflict**: Burnt Coral/Amber (HEX: #ff7f50 / #ffbf00) - Used for traps, conflicts, and blocked executions.
- **Neutral**: Slate 400-600 for secondary data and metadata labels.

## 3. Typography
- **Primary**: Inter (UI elements, headers)
- **Data Display**: JetBrains Mono (Arrays, metrics, tabular data) - Always use for focal contrast against dark backgrounds.

## 4. UI Patterns
- **Industrial Borders**: Thin (1px) borders with subtle opacity (white/10) and primary accent corners.
- **Scan Lines**: Subtle horizontal or vertical scan-line animations for a "live feed" feel.
- **High Contrast Tags**: Use `[TAG_NAME]` style for critical status indicators instead of just color.
- **Data Density**: High-density layouts with logical groupings. No wasted space or "bubbly" padding.

## 5. Anti-Patterns (NEVER USE)
- No "Hacker Green" or glowing neon borders.
- No Web3/Gamification/Confetti.
- No rounded, bubbly "Robinhood" style buttons.
- No pure black (#000) or pure white (#fff) without tinting.

## 6. Design System Notes for Stitch Generation (COPY THIS)
> **AESTHETIC**: Industrial Terminal. 
> **THEME**: Cold, predatory omniscience. Mechanical detachment.
> **PALETTE**: Slate 950 base. Muted cyan (#25d1f4) for success/support. Burnt coral for traps/alerts.
> **ELEMENTS**: Use `JetBrains Mono` for all data tables and metrics. Add thin borders with accent corners. Implement "scan-line" overlays on primary dashboards. Supplement all color indicators with text-based high-contrast tags like `[CONFLUENCE]`, `[CONFLICT]`, or `[WATCH]`.
