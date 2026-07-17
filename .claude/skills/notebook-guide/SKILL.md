---
name: notebook-guide
description: >
  Create well-structured Jupyter learning notebooks for AI engineering topics
  (LangChain, RAG, agents, embeddings, prompt engineering, evals) and general
  Python/data topics. Use this skill whenever the user asks to create a notebook,
  build a tutorial, make a learning guide, study a new AI/LLM concept hands-on,
  or turn a topic into runnable lessons — even if they don't say the word
  "notebook" (e.g. "help me learn RAG with code", "make me a LangChain
  walkthrough", "I want to practice building agents"). Also use it when
  improving or reviewing an existing .ipynb for structure and pedagogy.
---

# Notebook Guide

Build Jupyter notebooks that teach — not just demos that run. The target reader
is someone with solid Python/SQL skills and a data science background who is
transitioning into AI engineering. They learn best by running code, breaking it,
and doing exercises, not by reading walls of text.

## Workflow

1. **Pin down the topic and level.** If the request is vague ("teach me
   LangChain"), pick a concrete, single-sitting scope (60–90 minutes of work)
   and state it in the notebook's intro. One notebook = one concept done well.
   A series of small notebooks beats one giant one.
2. **Scaffold the notebook** with `scripts/scaffold_notebook.py` (see below)
   instead of hand-writing `.ipynb` JSON. Then fill in cells with NotebookEdit.
3. **Consult the references:**
   - `references/notebook-structure.md` — the section-by-section anatomy every
     learning notebook follows, with markdown cell templates.
   - `references/topic-guides.md` — what a good notebook covers for each AI
     engineering topic (RAG, agents, LangChain, embeddings, evals, prompting),
     including the classic pitfalls to demonstrate.
4. **Make every cell runnable top-to-bottom.** Restart-and-run-all must work.
   If a cell needs an API key, check for it early and fail with a clear message
   (see Setup rules below).
5. **End with exercises**, not a summary alone. Learning happens when the
   reader modifies code, so leave 2–4 exercises with TODO cells and a
   collapsed/optional solutions section.

## Structure every notebook follows

```
1. Title + What you'll learn (3-5 bullet objectives)
2. Prerequisites & Setup (installs, imports, API-key check)
3. Concept sections (2-4 of them), each:
   - Short markdown explanation (why before how, <150 words)
   - Minimal runnable example
   - A variation or "what happens if..." cell
4. Common pitfalls (show at least one failure mode actually happening)
5. Exercises (TODO cells the reader completes)
6. Recap + Where to go next (links, and the next notebook in the series)
```

Full templates and rationale: `references/notebook-structure.md`.

## Scaffolding

Generate a valid notebook skeleton in one command:

```bash
python .claude/skills/notebook-guide/scripts/scaffold_notebook.py \
  notebooks/03_rag_basics.ipynb \
  --title "RAG Basics: Retrieval-Augmented Generation from Scratch" \
  --objectives "Explain the retrieve-then-generate loop" \
               "Build a tiny vector store with numpy" \
               "Wire retrieval into an LLM prompt" \
  --sections "Why RAG exists" "Embedding and storing documents" \
             "Retrieval" "Putting it together"
```

The script writes a `.ipynb` with the standard structure (title, objectives,
setup cell, one markdown+code pair per section, pitfalls, exercises, recap)
so you only fill in content. It never overwrites an existing file.

## Conventions for this repo

- Put notebooks in a `notebooks/` directory, numbered in learning order:
  `01_embeddings.ipynb`, `02_vector_search.ipynb`, ...
- This project uses **uv**. Add notebook dependencies with
  `uv add --group notebooks <pkg>` rather than `pip install` in cells; the
  setup cell should verify imports and tell the reader the `uv` command to run
  if one is missing. (`jupyter`/`ipykernel` belong in that group too.)
- Never hardcode API keys. Load from environment via `python-dotenv`
  (already a dependency) and check presence in the setup cell:
  a missing key should produce one clear actionable message, not a traceback
  ten cells later.
- Prefer small local/free examples first (numpy cosine similarity, tiny
  document lists, stub LLM functions) so most of the notebook runs without
  paid API calls; mark the cells that do call an API.

## Style rules for cells

- Markdown cells explain **why**; code comments explain only non-obvious
  **how**. Don't duplicate the markdown in comments.
- Keep code cells under ~20 lines; split longer logic so intermediate results
  are visible. Ending a cell with an expression (not `print`) shows rich
  output — use it.
- Show real outputs worth looking at: print shapes, a few retrieved chunks,
  token counts — not silent cells.
- When demonstrating a pitfall, actually run the broken version and show the
  bad result before showing the fix. Seeing failure is the lesson.
