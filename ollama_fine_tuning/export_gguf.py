"""
Step 3: Merge LoRA adapter + base model and export to GGUF for Ollama.

Usage:
    python export_gguf.py
    python export_gguf.py --adapter model_output --quantization q5_k_m

Then:
    ollama create my-model -f Modelfile
    ollama run my-model
"""

import argparse

from unsloth import FastLanguageModel


QUANT_METHODS = ["q8_0", "q6_k", "q5_k_m", "q4_k_m", "q4_0", "q3_k_m"]


def main():
    parser = argparse.ArgumentParser(description="Export to GGUF for Ollama")
    parser.add_argument("--adapter", default="model_output", help="Trained adapter path")
    parser.add_argument("--output", default="model_gguf", help="GGUF output directory")
    parser.add_argument("--quantization", default="q4_k_m", choices=QUANT_METHODS)
    parser.add_argument("--max-seq-length", type=int, default=2048)
    args = parser.parse_args()

    print(f"Loading adapter from {args.adapter}...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.adapter,
        max_seq_length=args.max_seq_length,
        load_in_4bit=True,
    )

    print(f"Exporting GGUF ({args.quantization})...")
    model.save_pretrained_gguf(args.output, tokenizer, quantization_method=args.quantization)

    print(f"\nDone! GGUF saved to {args.output}/")
    print(f"Next: ollama create my-model -f Modelfile")


if __name__ == "__main__":
    main()
