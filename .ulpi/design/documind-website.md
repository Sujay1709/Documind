# DocuMind website UX specification

This feature binds to `.ulpi/design/DESIGN.md`.

## Primary flow

1. User lands on the upload workspace.
2. User chooses or drops one or more PDFs.
3. The upload surface becomes an indexing state and prevents duplicate submissions.
4. On success, the first uploaded source becomes the visible scope and the conversation opens.
5. User selects a source or "All documents", asks a question, and receives streamed answer text plus
   expandable citations.
6. If retrieval or generation fails, the conversation preserves the question and shows an actionable
   error without pretending the answer completed.

## State coverage

| Surface | Empty | Loading | Success | Error | Edge cases |
| --- | --- | --- | --- | --- | --- |
| Document list | No documents indexed | Loading documents | Count and scope selector | Server unavailable | Refresh while chatting |
| Upload | Choose/drop PDF | Indexing, controls disabled | Indexed names and selected source | Inline upload error | Multiple files, invalid MIME, duplicate drop |
| Composer | Ask about documents | Streaming with stop/disabled action | Answer and sources | Error message with preserved question | Offline, expired token |
| Sources | No citations | Waiting for retrieval | File/page/score/snippet | No relevant chunks | Long filenames and snippets |
| Theme | Stored preference | N/A | Dark/light | Storage unavailable | First paint must match preference |

## Component rules

### Workbench header

Purpose: establish product identity and expose document count, search scope, admin state, and theme.
On mobile, scope moves to a full-width row; secondary metadata disappears before controls do.
Every control has an accessible name and a visible focus ring.

### Upload surface

Use one primary action: "Choose PDF". Drop state changes border and helper text, not the entire
layout. Indexing shows "Indexing..." and disables the input. Errors use `role="status"` and remain
visible until the next attempt.

### Conversation

User and assistant messages use one ruled message surface with clear role and time metadata. The
assistant state must distinguish "Thinking" from an interrupted or failed stream. Citations are
progressive disclosure, open by default only for the newest completed answer.

### Composer

The selected scope is adjacent to the composer, not hidden in a separate settings view. Enter sends;
Shift+Enter inserts a newline. The send control remains at least 44px square and exposes its busy
state to assistive technology.

## Accessibility and responsive acceptance

- Full keyboard path: scope selector, admin, theme, upload, suggestions, composer, send, citations.
- `aria-label` or visible label on every icon-only action.
- `role="status"` for indexing, server availability, and generation interruption.
- Reduced motion disables decorative movement and staggered reveals.
- At 720px and below, no horizontal overflow; scope selector and footer wrap.
- Essential copy never relies on muted text alone or color alone.

## Build handoff

Target: React/Vite frontend engineer.

Implement exactly this specification using the tokens in `DESIGN.md`; do not redesign or replace
the component system. Existing UI changes already cover scope selection, upload locking, server
errors, focus styles, theme first paint, and mobile 3D reduction. Future UI work should close the
remaining generation cancellation and citation-state gaps without reintroducing decorative effects.

## Pre-flight result

- Identity lock: PASS. One token set, one type pairing, one icon approach.
- Anti-slop: PASS. Technical/utilitarian direction; no new gradients, nested cards, fake metrics, or
  generic AI marketing copy.
- State and flow coverage: PASS. Empty, loading, success, error, offline, refresh, and token edges
  are specified.
- Accessibility: PASS. Focus, keyboard, ARIA status, reduced motion, contrast, and touch targets
  are specified.
- Layout craft: PASS. Upload workspace, conversation evidence view, and responsive scope rail are
  distinct layout families.
- Cognitive load: PASS. One primary action per view and one visible scope decision.
- Self-critique: distinctiveness 3, hierarchy 4, consistency 4, accessibility 3, state coverage 4,
  copy quality 3, restraint 4, motion motivation 3. Total 28/32.
