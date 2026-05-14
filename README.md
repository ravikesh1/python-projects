# PDF RAG — Study Notebook

A minimal Retrieval-Augmented Generation pipeline over a PDF, built as a Jupyter notebook.

## Quick start (VSCode + uv)

```bash
uv sync
cp .env.example .env   # add your ANTHROPIC_API_KEY
mkdir -p data
# drop any PDF as data/sample.pdf
```

Then open `pdf_rag.ipynb` in VSCode and pick the kernel from `.venv/bin/python`.

## What you get

| Step | What |
|------|------|
| 1    | Imports & config |
| 2    | Extract text per page from PDF (`pypdf`) |
| 3    | Chunk text with overlap (`langchain-text-splitters`) |
| 4    | Embed chunks locally (`sentence-transformers`) |
| 5    | Persist to a local vector DB (`chromadb`) |
| 6    | Retrieve top-k chunks for a question |
| 7    | Generate a grounded, cited answer with Claude |
| 8    | Experiment: tune `k`, chunk size, embedding model |
