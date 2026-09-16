# DocuMind design language

## Design read

DocuMind should feel like a quiet document workbench, not an AI novelty surface. The visual bet is
that trust comes from readable evidence, calm hierarchy, and visible system state.

## Aesthetic direction

**Technical / utilitarian.** The product is a local retrieval tool used while reading and checking
documents. Its identity is a restrained instrument panel: ruled surfaces, precise labels, compact
controls, and one high-signal accent. It deliberately rejects generic chatbot neon, decorative
glass on every element, and centered marketing hero composition.

Counterfactual test: this is not the default look for an AI chat product because the primary
interaction is an evidence rail and document scope, not a glowing assistant persona.

## Register and system

- Register: product UI.
- System: CSS tokens and semantic HTML over the existing React/Vite app. Do not add a component
  library for this surface.
- Icon family: compact text/Unicode icons only where they have a visible label; no mixed icon packs.
- Signature: the active document scope is always visible beside the question composer, with a clear
  "All documents" state.

## Tokens

### Color

Use the existing dark/light theme variables as implementation tokens, but keep the visual hierarchy
below:

- Canvas: deep ink in dark mode, cool mist in light mode.
- Surface: opaque enough for reading; translucency is reserved for the app shell and composer.
- Text: high-contrast ink.
- Muted text: metadata only, never essential instructions.
- Accent: electric blue for one primary action and focus ring.
- Semantic red: errors and interrupted generation only.

Text must meet WCAG AA: 4.5:1 for normal text, 3:1 for large text and controls. Focus indicators
must remain visible in both themes.

### Type

- Display: the existing system sans in 800 weight for the product name and single focal heading.
- Body: system sans at 15-16px with 1.55 line height.
- Metadata: system sans at 12-13px with increased letter spacing.
- Do not introduce a second decorative typeface.

### Geometry and motion

- Spacing scale: 4, 8, 12, 16, 24, 32.
- Radius scale: 10px controls, 16px messages, 20px upload surface, pill only for scope/status.
- Motion: one page-load reveal plus short state transitions. No infinite motion except the streaming
  cursor. Respect `prefers-reduced-motion`.
- Touch targets: minimum 44px.

## Voice

Concrete, local, and honest. Prefer "Indexing document" over "Making magic happen". Never promise
that an answer is correct; show sources and explain when the server or model is unavailable.
