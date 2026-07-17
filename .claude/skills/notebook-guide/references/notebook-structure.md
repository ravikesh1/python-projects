# Notebook Structure Reference

The section-by-section anatomy of a learning notebook, with markdown cell
templates and the reasoning behind each section. Follow this order unless the
topic genuinely demands otherwise.

## Contents

1. [Title & objectives](#1-title--objectives)
2. [Setup](#2-setup)
3. [Concept sections](#3-concept-sections)
4. [Common pitfalls](#4-common-pitfalls)
5. [Exercises](#5-exercises)
6. [Recap & next steps](#6-recap--next-steps)
7. [Series conventions](#7-series-conventions)

---

## 1. Title & objectives

The first cell sells the notebook and sets expectations. A reader should know
in 10 seconds whether this is the right notebook for them and what they'll be
able to *do* afterwards.

Template:

```markdown
# RAG Basics: Retrieval-Augmented Generation from Scratch

**What you'll learn:**

- Explain the retrieve-then-generate loop and why it beats stuffing everything in the prompt
- Build a tiny vector store with numpy and cosine similarity
- Wire retrieval results into an LLM prompt and see the answer quality change

**Time:** ~75 minutes | **Prerequisites:** Python, basic numpy; notebook 01 (embeddings)
```

Objectives are *verbs the reader performs* ("build", "explain", "debug"), not
topics ("overview of RAG"). 3–5 objectives; more means the scope is too big —
split the notebook.

## 2. Setup

One markdown cell + one code cell. The code cell must:

- Check required imports and, on failure, print the exact `uv add --group
  notebooks ...` command to fix it — then stop. A reader who hits an obscure
  `ModuleNotFoundError` in cell 14 loses trust in the whole notebook.
- Load `.env` with `python-dotenv` and verify any required API keys are
  present, again failing with one actionable message.
- End with a visible success signal (`print("Setup OK")`).

Never `pip install` inside cells: this repo manages environments with uv, and
in-cell installs silently desync the lockfile from reality.

## 3. Concept sections

2–4 sections, each following **explain → run → vary**:

1. **Markdown: the why.** Under 150 words. Answer "what problem does this
   solve?" before any mechanics. Analogies to things the reader already knows
   (SQL, pandas, classic ML) land especially well for this audience.
2. **Code: minimal runnable example.** The smallest complete thing that
   demonstrates the idea. Under ~20 lines. End the cell with an expression so
   the rich repr shows (a DataFrame, a list of retrieved chunks, a dict of
   scores) rather than a bare `print`.
3. **Code: a variation.** Change one input or parameter and observe the
   behavior change. This is what converts "I read it" into "I get it":
   temperature 0 vs 1, k=1 vs k=5 retrieval, chunk size 100 vs 1000.

Section headings are numbered (`## 1. Why RAG exists`) so the reader can track
progress and you can reference sections from the recap.

If a section needs more than one example, that's usually a sign it should be
two sections — or its own notebook.

## 4. Common pitfalls

Show at least one failure mode *actually happening* — run the broken version,
display the bad output, then fix it. Reading "be careful about X" teaches
nothing; watching X produce garbage and then seeing the one-line fix is
memorable.

Good pitfall demos per topic are listed in `topic-guides.md`.

Template:

```markdown
## Common pitfalls

### Pitfall: chunks too large

Watch what happens to retrieval quality when whole documents are embedded as
single chunks:
```

(then the broken code cell, its poor output, and the corrected cell.)

## 5. Exercises

2–4 exercises as TODO code cells. Order them from "modify one line of the
example" to "combine two sections' ideas". Each exercise states what success
looks like so the reader can self-check:

```python
# Exercise 2: Change the retriever to return the top-3 chunks instead of top-1,
# and pass all three into the prompt.
# Success check: the answer to the multi-document question below should now
# mention both the refund policy AND the shipping time.

# TODO: your code here
```

Put solutions at the bottom inside a collapsed `<details>` block, or in a
separate `solutions/` notebook for a series. Never inline solutions right
under the exercise — proximity kills the attempt.

## 6. Recap & next steps

- 3–5 bullets restating the objectives as things now accomplished.
- Explicit pointer to the next notebook in the series.
- 1–2 curated further-reading links (official docs, one great article) — not
  a link dump.

## 7. Series conventions

- Directory: `notebooks/`, numbered in learning order:
  `01_embeddings.ipynb`, `02_vector_search.ipynb`, `03_rag_basics.ipynb`.
- Each notebook's prerequisites line names the notebooks it builds on.
- Shared helper code that multiple notebooks need goes in a small module
  (e.g. `notebooks/helpers.py`), imported at setup — not copy-pasted between
  notebooks where copies drift apart.
- Data files live in `notebooks/data/`; keep them tiny (KBs, not MBs) and
  committed, so restart-and-run-all works on a fresh clone.
