# RAFT and LoRA plan for DocuMind

## Three priority gaps

1. **Hierarchical evidence navigation** - vector similarity currently finds chunks, but
   users need page/section context to verify an answer and the model benefits from
   adjacent passages. PageIndex-style metadata and grouped retrieval now provide this
   without replacing Chroma.
2. **Generation recovery controls** - a browser client should be able to cancel a
   stream, retry a failed generation without duplicating partial text, and resume from
   the preserved question and citations. The backend retry guard only covers failures
   before the first token, so the next step is an explicit request/stream lifecycle
   state machine.
3. **Quality gates for domain adaptation** - the project has evaluation metrics, but a
   training or prompt change needs a held-out regression gate covering retrieval,
   groundedness, citation validity, refusal behavior, and stream failures. Without that,
   fine-tuning can improve style while silently reducing evidence use.

## What RAFT contributes

The attached RAFT paper (arXiv:2403.10131v2, June 2024) describes Retrieval Augmented
Fine-Tuning for fixed-domain, open-book question answering. Each training example contains
a question, one answer-bearing ("golden") document, and irrelevant retrieved documents
("distractors"). The target includes a verbatim quote from the useful context followed by
reasoning and the answer. The model therefore learns both to read retrieved text and to
ignore plausible but irrelevant passages.

The paper reports that training only on golden context is less robust. Their experiments
mix examples without the golden document and commonly use one golden document with four
distractors, while the best golden-document proportion varies by dataset. The paper also
finds that a reason-plus-answer target is stronger than an answer-only target. These
results apply to a fixed in-domain corpus; they do not mean that fine-tuning should replace
retrieval or that chain-of-thought should be exposed to end users.

## DocuMind dataset format

Generate JSONL offline from indexed chunks and reviewed questions:

```json
{
  "question": "What is the retention period?",
  "documents": [
    {"id": "policy_pdf_12", "text": "...", "source": "policy_pdf", "page": 12, "role": "gold"},
    {"id": "policy_pdf_04", "text": "...", "source": "policy_pdf", "page": 4, "role": "distractor"}
  ],
  "answer": "Seven years.",
  "quote": "Records must be retained for seven years.",
  "reason": "The quoted policy sentence states the duration directly.",
  "citations": [{"source": "policy_pdf", "page": 12}]
}
```

Build examples by:

1. Sampling a question whose answer is supported by a chunk or section.
2. Selecting the golden chunk and 2-4 same-corpus distractors from other pages or
   documents, preserving realistic retrieval noise.
3. Keeping a portion of examples without the golden chunk to teach abstention and
   prevent reliance on a fixed context position.
4. Generating candidate quotes/reasons only with a model, then validating citations
   against the source text and manually reviewing a held-out sample.
5. Splitting by document, not by question, so near-duplicate pages cannot leak from
   training into evaluation.

At inference, keep the existing RAG pipeline. Fine-tuning should teach context selection,
citation style, and domain answer format; it should not be used as the document database.

## LoRA/QLoRA workflow

Use a separate Python training environment with Hugging Face Transformers, PEFT, TRL,
and optionally bitsandbytes or Unsloth. Start with QLoRA on a 7B-8B instruct model that
is compatible with the available GPU. Train adapters, not the base model:

The repository provides the dataset builder, but intentionally does not bundle a GPU
training stack. After installing your chosen Transformers/PEFT/TRL environment, run
your training entry point with the generated files:

```bash
documind-raft \
  --questions data/raft/questions.json \
  --documents data/raft/documents.json \
  --out data/raft/train.jsonl

accelerate launch <your-qlora-training-script> \
  --base-model <instruct-model> \
  --train-data data/raft/train.jsonl \
  --eval-data data/raft/heldout.jsonl \
  --output-dir artifacts/documind-raft-lora
```

Keep the adapter artifact outside the application repository when it is large. Evaluate
the base model, base+RAG, LoRA+no-context, and LoRA+RAG using the same held-out questions.
Promote an adapter only if retrieval hit/recall, groundedness, citation validity, refusal
accuracy, and answer quality do not regress beyond agreed thresholds.

Ollama is the serving layer, not the training layer. After evaluation, either merge the
adapter into the base model or export a compatible quantized model, convert it to the
format supported by the installed Ollama version, and register it with a `Modelfile`.
Keep the original model and adapter so rollback is possible. Do not fine-tune embeddings
and the generator in the same experiment: retrieval changes and generator changes need
separate ablations.

## Safety and evaluation gates

- Never train on secrets, private credentials, or unreviewed user uploads.
- Preserve source/page metadata and verify every generated citation.
- Add no-answer and conflicting-document examples.
- Track token cost, latency, first-token failures, mid-stream failures, and retry counts.
- Require a non-zero evaluation exit code for a failed regression gate.
- Keep chain-of-thought as an internal training scaffold; expose only concise answers,
  quotes, and citations in the UI.

The dataset generator and runtime grounding safeguards are implemented now. The next
implementation slice should add a deterministic `documind-eval --gate` command and run
the actual adapter training only after the base model, GPU budget, and document
licensing are selected.
