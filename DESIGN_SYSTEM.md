# Design System: Kinetic Brutalism

This document outlines the design principles and component styles for the "No-Ledge" application. The goal is to create a visually striking, technically impressive, and memorable user experience by combining the raw, functional aesthetic of Brutalism with a dynamic, interactive SVG background.

## Core Philosophy: Dynamic Contrast

The entire design language is built on a single, powerful idea: **the contrast between a static, rigid foreground and a fluid, organic background.**

*   **Foreground (UI):** Uncompromisingly brutalist. It is functional, clear, and raw. It feels like a piece of industrial hardware or a command-line interface.
*   **Background (Experience):** Constantly in motion. The interactive "gooey" SVG effect provides a sense of life and responsiveness, making the application feel alive and intriguing.

This contrast is what creates the "how did they do that?" effect.

---

## 1. Color Palette

The palette is minimal, high-contrast, and aggressive.

| Role            | Color Name     | Hex Code  | Usage                               |
| --------------- | -------------- | --------- | ----------------------------------- |
| **Background**  | `var(--bg)`    | `#000000` | The base for all UI components.     |
| **Foreground**  | `var(--fg)`    | `#FFFFFF` | Primary text and standard borders.  |
| **Accent**      | `var(--accent)`| `#FFFF00` | Interactive elements, highlights, links, and the SVG background blobs. |

---

## 2. Typography

We use a single monospace font to reinforce the technical, terminal-like feel of the UI.

*   **Font Family:** `Source Code Pro`, served via Google Fonts.
*   **Weights:** `400` (Regular) for body text and `600` (Semi-bold) for headings and important labels.
*   **Styling:** All text is sharp, with anti-aliasing enabled for readability.

---

## 3. Core Components

All components adhere to the "no curves, no shadows" rule of Brutalism.

### Borders

*   **Standard Border:** `2px solid var(--fg)` (`#FFFFFF`). Used for cards, forms, and containers.
*   **Accent Border:** `2px solid var(--accent)` (`#FFFF00`). Used for focused form elements.

### Cards (`.glass-card`)

*   **Appearance:** A simple rectangle with a standard white border on a black background.
*   **Spacing:** Consistent internal padding (`2rem`) to ensure content breathes.
*   **No `border-radius`**, **No `box-shadow`**.

### Buttons (`.btn-primary`)

*   **Appearance:** A solid block of the accent color (`#FFFF00`) with black text. Has a standard white border.
*   **Interaction (`:hover`):** The button shifts position (`transform: translate(4px, 4px)`) and reveals a solid white "shadow" behind it. This creates a tactile, physical feel without using traditional gradients or shadows.
*   **No `border-radius`**.

### Forms (`.form-control`, `.form-select`)

*   **Appearance:** Black background, white text, and a standard white border.
*   **Interaction (`:focus`):** The border color changes to the accent yellow (`#FFFF00`) to provide clear visual feedback.
*   **No `border-radius`**.

### Links (`a`)

*   **Appearance:** Underlined and colored with the accent yellow (`#FFFF00`).
*   **Interaction (`:hover`):** The background becomes yellow and the text becomes black, creating an inverted, high-contrast effect.

---

## 4. The SVG Background

*   **Effect:** A "Gooey" or "Metaball" effect created using an SVG filter. Multiple blobs merge and separate like liquid mercury.
*   **Technology:** The effect relies on `<feGaussianBlur>` to blur the shapes and `<feColorMatrix>` to sharpen the alpha channel, creating the merge effect at the edges.
*   **Interactivity:** The background tracks the user's mouse, with a central blob following the cursor and influencing the surrounding blobs. This makes the user an active participant in the visual experience.

By adhering to this system, we ensure that "No-Ledge" maintains a consistent, bold, and technically fascinating identity.
