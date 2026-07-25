"""
Step 1: Convert PDFs into training data.

Reads PDFs, chunks the text, and generates instruction/response
pairs as JSONL. Two modes:

  Manual:  Generates pairs with placeholder outputs for you to fill in.
  Auto:    Uses a running Ollama model to generate the responses.

Usage:
    python prepare_data.py --pdf-dir ./pdfs
    python prepare_data.py --pdf-dir ./pdfs --auto-generate --model llama3.2
"""

import argparse
import json
import os

from pypdf import PdfReader


def extract_pages(pdf_path: str) -> list[dict]:
    """Extract text from each page of a PDF."""
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"text": text, "page": i + 1, "source": os.path.basename(pdf_path)})
    return pages


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c.strip() for c in chunks if len(c.strip()) >= 50]


TEMPLATES = [
    ("Summarize the following text.", "summary"),
    ("What are the key points in this section?", "key_points"),
    ("Extract the main facts and findings from this text.", "extraction"),
    ("What does this section discuss?", "qa"),
]


def make_training_pairs(pages: list[dict], chunk_size: int, overlap: int) -> list[dict]:
    """Generate instruction/input/output triples from PDF pages."""
    pairs = []
    for page in pages:
        chunks = chunk_text(page["text"], chunk_size, overlap)
        for chunk in chunks:
            for instruction, task in TEMPLATES:
                pairs.append({
                    "instruction": instruction,
                    "input": chunk,
                    "output": f"<FILL:{task}>",
                    "meta": {"source": page["source"], "page": page["page"]},
                })
    return pairs


def auto_fill_responses(pairs: list[dict], model: str, base_url: str) -> list[dict]:
    """Use Ollama to generate responses for training pairs."""
    import requests

    total = len(pairs)
    for i, pair in enumerate(pairs, 1):
        prompt = f"{pair['instruction']}\n\nText:\n{pair['input']}\n\nResponse:"

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            if resp.status_code == 200:
                pair["output"] = resp.json()["response"].strip()
                print(f"  [{i}/{total}] OK ({len(pair['output'])} chars)")
            else:
                print(f"  [{i}/{total}] HTTP {resp.status_code}")
        except Exception as e:
            print(f"  [{i}/{total}] Error: {e}")

    return pairs


def main():
    parser = argparse.ArgumentParser(description="Prepare training data from PDFs")
    parser.add_argument("--pdf-dir", required=True, help="Directory with PDF files")
    parser.add_argument("--output", default="data/training.jsonl", help="Output JSONL path")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    parser.add_argument("--auto-generate", action="store_true", help="Use Ollama for responses")
    parser.add_argument("--model", default="llama3.2", help="Ollama model for auto-generation")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    args = parser.parse_args()

    pdfs = [f for f in os.listdir(args.pdf_dir) if f.lower().endswith(".pdf")]
    if not pdfs:
        print(f"No PDFs in {args.pdf_dir}")
        return

    all_pairs = []
    for pdf in pdfs:
        path = os.path.join(args.pdf_dir, pdf)
        print(f"Processing {pdf}...")
        pages = extract_pages(path)
        pairs = make_training_pairs(pages, args.chunk_size, args.chunk_overlap)
        all_pairs.extend(pairs)
        print(f"  {len(pages)} pages -> {len(pairs)} training pairs")

    if args.auto_generate:
        print(f"\nGenerating responses with {args.model}...")
        all_pairs = auto_fill_responses(all_pairs, args.model, args.ollama_url)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        for pair in all_pairs:
            out = {k: v for k, v in pair.items() if k != "meta"}
            f.write(json.dumps(out) + "\n")

    placeholders = sum(1 for p in all_pairs if p["output"].startswith("<FILL"))
    print(f"\nWrote {len(all_pairs)} examples to {args.output}")
    if placeholders:
        print(f"{placeholders} still have placeholders — re-run with --auto-generate or edit manually")


if __name__ == "__main__":
    main()
