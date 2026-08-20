# Eval datasets

`realistic.json` is the dataset the benchmark runs against — 8 questions
spanning the four document types most users would actually upload
(resume, structured framework summary, textbook chapter, EDA report).
Every question has:

- `ground_truth` — a short reference answer used for token-F1.
- `expected_sources` — the indexed document name (as it appears in
  Chroma) the answer should be drawn from, used for hit/recall/MRR.
- `expected_keywords` — terms that must appear for the answer to count
  as grounded.

`sample_dataset.json` is the original 2-question example kept for the
`make eval` smoke run; it covers two unrelated topics so the smoke
test can prove end-to-end wiring without needing your local corpus.

## How to add questions

1. Upload the source document in the app (or via the ingestion API) and
   copy the *normalised* source name from the sidebar's "Indexed
   documents" list (dots/dashes/spaces become underscores).
2. Write the question, ground-truth answer, expected source, and 1–3
   keywords that should appear.
3. Add it to `realistic.json` (or a new dataset file).
4. Re-run `make benchmark`.

The eval harness is forgiving — missing `ground_truth` simply skips
F1, missing `expected_sources` skips the retrieval metrics, etc. So you
can add questions incrementally without bookkeeping for every field.
