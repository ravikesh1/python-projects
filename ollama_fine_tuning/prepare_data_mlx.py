"""
Prepare training data for MLX fine-tuning on Apple Silicon.

MLX expects train.jsonl / valid.jsonl / test.jsonl with a "text" field
containing the full formatted prompt. This script:
  1. Reads PDFs and chunks them
  2. Generates instruction/response pairs (optionally via Ollama)
  3. Splits into train/valid/test and writes MLX-format JSONL

Usage:
    python prepare_data_mlx.py --pdf-dir ./pdfs --auto-generate --model llama3.2
"""

import argparse
import json
import os
import random

from pypdf import PdfReader


PROMPT_TEMPLATE = """### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""

TEMPLATES = [
    "Summarize the following text.",
    "What are the key points in this section?",
    "Extract the main facts and findings from this text.",
    "What does this section discuss?",
]


def extract_pages(pdf_path: str) -> list[dict]:
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"text": text, "page": i + 1, "source": os.path.basename(pdf_path)})
    return pages


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c.strip() for c in chunks if len(c.strip()) >= 50]


def make_pairs(pages: list[dict], chunk_size: int, overlap: int) -> list[dict]:
    pairs = []
    for page in pages:
        chunks = chunk_text(page["text"], chunk_size, overlap)
        for chunk in chunks:
            for instruction in TEMPLATES:
                pairs.append({
                    "instruction": instruction,
                    "input": chunk,
                    "output": f"<FILL>",
                })
    return pairs


def auto_fill(pairs: list[dict], model: str, base_url: str) -> list[dict]:
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
                print(f"  [{i}/{total}] OK")
            else:
                print(f"  [{i}/{total}] HTTP {resp.status_code}")
        except Exception as e:
            print(f"  [{i}/{total}] Error: {e}")
    return pairs


def format_for_mlx(pair: dict) -> dict:
    """Convert instruction/input/output to MLX text format."""
    text = PROMPT_TEMPLATE.format(**pair)
    return {"text": text}


def split_and_write(pairs: list[dict], output_dir: str, train_ratio: float = 0.8):
    """Split data 80/10/10 and write train/valid/test JSONL."""
    random.shuffle(pairs)
    n = len(pairs)
    train_end = int(n * train_ratio)
    valid_end = int(n * (train_ratio + 0.1))

    splits = {
        "train.jsonl": pairs[:train_end],
        "valid.jsonl": pairs[train_end:valid_end],
        "test.jsonl": pairs[valid_end:],
    }

    os.makedirs(output_dir, exist_ok=True)
    for filename, data in splits.items():
        path = os.path.join(output_dir, filename)
        with open(path, "w") as f:
            for pair in data:
                f.write(json.dumps(format_for_mlx(pair)) + "\n")
        print(f"  {filename}: {len(data)} examples")


def main():
    parser = argparse.ArgumentParser(description="Prepare MLX training data from PDFs")
    parser.add_argument("--pdf-dir", required=True, help="Directory with PDF files")
    parser.add_argument("--output-dir", default="data", help="Output directory for JSONL files")
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
        pairs = make_pairs(pages, args.chunk_size, args.chunk_overlap)
        all_pairs.extend(pairs)
        print(f"  {len(pages)} pages -> {len(pairs)} pairs")

    if args.auto_generate:
        print(f"\nGenerating responses with {args.model}...")
        all_pairs = auto_fill(all_pairs, args.model, args.ollama_url)

    usable = [p for p in all_pairs if not p["output"].startswith("<FILL")]
    if not usable:
        print("\nNo usable pairs — re-run with --auto-generate or edit data manually")
        return

    print(f"\nSplitting {len(usable)} examples into train/valid/test...")
    split_and_write(usable, args.output_dir)
    print("Done!")


if __name__ == "__main__":
    main()
