"""
Step 1: Convert PDFs into training data (instruction/response JSONL).

This script reads PDFs and generates training pairs in three styles:
  - Summarization: "Summarize this section" → summary
  - Q&A: "Answer based on this context" → answer
  - Extraction: "Extract key information" → structured extraction

Usage:
    python prepare_data.py --pdf-dir ./pdfs --output data/training.jsonl

You'll want to review and edit the output — quality of training data
directly determines quality of the fine-tuned model.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pdf_processor import load_pdf, split_documents


TEMPLATES = [
    {
        "instruction": "Summarize the following text from the document '{source}' (page {page}).",
        "task": "summary",
    },
    {
        "instruction": "What are the key points in the following section from '{source}'?",
        "task": "key_points",
    },
    {
        "instruction": "Based on the following context from '{source}', extract the main facts and findings.",
        "task": "extraction",
    },
    {
        "instruction": "Answer questions using only the following context from '{source}' (page {page}). What does this section discuss?",
        "task": "qa",
    },
]


def format_training_example(instruction: str, context: str, response: str) -> dict:
    """Format a single training example in Alpaca/chat format."""
    return {
        "instruction": instruction,
        "input": context,
        "output": response,
    }


def generate_pairs_from_chunks(chunks: list, source_name: str) -> list[dict]:
    """Generate raw training pairs from document chunks.

    These pairs have placeholder outputs — you need to fill them in
    manually or use a strong model to generate initial responses.
    """
    pairs = []
    for chunk in chunks:
        page = chunk.metadata.get("page", 0)
        content = chunk.page_content.strip()

        if len(content) < 50:
            continue

        for template in TEMPLATES:
            instruction = template["instruction"].format(
                source=source_name,
                page=page,
            )
            pairs.append(
                format_training_example(
                    instruction=instruction,
                    context=content,
                    response=f"<FILL: {template['task']} response for this chunk>",
                )
            )

    return pairs


def generate_with_ollama(pairs: list[dict], model: str, base_url: str) -> list[dict]:
    """Use a running Ollama model to auto-generate training responses.

    This bootstraps your training data using a stronger model's output.
    Review the generated responses before training.
    """
    import requests

    filled = []
    total = len(pairs)

    for i, pair in enumerate(pairs, 1):
        prompt = (
            f"Instruction: {pair['instruction']}\n\n"
            f"Context:\n{pair['input']}\n\n"
            f"Provide a clear, concise response:"
        )

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            if resp.status_code == 200:
                pair["output"] = resp.json()["response"].strip()
                print(f"  [{i}/{total}] Generated response ({len(pair['output'])} chars)")
            else:
                print(f"  [{i}/{total}] Failed: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  [{i}/{total}] Error: {e}")

        filled.append(pair)

    return filled


def main():
    parser = argparse.ArgumentParser(description="Prepare fine-tuning data from PDFs")
    parser.add_argument("--pdf-dir", required=True, help="Directory containing PDF files")
    parser.add_argument("--output", default="data/training.jsonl", help="Output JSONL file")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    parser.add_argument(
        "--auto-generate",
        action="store_true",
        help="Use Ollama to auto-generate responses (requires Ollama running)",
    )
    parser.add_argument("--model", default="llama3.2", help="Ollama model for auto-generation")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    args = parser.parse_args()

    all_pairs = []

    pdf_files = [f for f in os.listdir(args.pdf_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in {args.pdf_dir}")
        return

    for pdf_file in pdf_files:
        pdf_path = os.path.join(args.pdf_dir, pdf_file)
        print(f"Processing {pdf_file}...")

        pages = load_pdf(pdf_path)
        chunks = split_documents(pages, args.chunk_size, args.chunk_overlap)
        pairs = generate_pairs_from_chunks(chunks, pdf_file)
        all_pairs.extend(pairs)
        print(f"  {len(pages)} pages → {len(chunks)} chunks → {len(pairs)} training pairs")

    if args.auto_generate:
        print(f"\nAuto-generating responses with {args.model}...")
        all_pairs = generate_with_ollama(all_pairs, args.model, args.ollama_url)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"\nWrote {len(all_pairs)} training examples to {args.output}")

    placeholder_count = sum(1 for p in all_pairs if p["output"].startswith("<FILL"))
    if placeholder_count:
        print(f"\n⚠ {placeholder_count} examples still have placeholder outputs.")
        print("  Edit the JSONL file or re-run with --auto-generate to fill them.")


if __name__ == "__main__":
    main()
