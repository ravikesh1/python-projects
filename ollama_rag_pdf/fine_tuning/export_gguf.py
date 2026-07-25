"""
Step 3: Merge LoRA adapter into base model and export to GGUF.

GGUF is the format Ollama uses. This script:
  1. Loads the base model + your trained LoRA adapter
  2. Merges them into a single model
  3. Exports to GGUF with quantization (q4_k_m = good quality/size balance)

Usage:
    python export_gguf.py --adapter model_output --output model_gguf

Then import into Ollama:
    ollama create my-model -f Modelfile
"""

import argparse

from unsloth import FastLanguageModel


MODEL_MAP = {
    "llama3.2-1b": "unsloth/Llama-3.2-1B-Instruct-bnb-4bit",
    "llama3.2-3b": "unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
    "llama3.1-8b": "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    "mistral-7b": "unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
    "phi-3.5": "unsloth/Phi-3.5-mini-instruct-bnb-4bit",
}

# Quantization methods ranked by quality vs size:
#   q8_0     - best quality, largest  (~8GB for 7B model)
#   q6_k     - very good quality      (~6GB)
#   q5_k_m   - good quality           (~5GB)
#   q4_k_m   - balanced (recommended) (~4GB)
#   q4_0     - smaller, lower quality (~3.5GB)
#   q3_k_m   - smallest usable        (~3GB)
QUANT_METHODS = ["q8_0", "q6_k", "q5_k_m", "q4_k_m", "q4_0", "q3_k_m"]


def main():
    parser = argparse.ArgumentParser(description="Export fine-tuned model to GGUF for Ollama")
    parser.add_argument("--adapter", default="model_output", help="Path to trained LoRA adapter")
    parser.add_argument("--output", default="model_gguf", help="Output directory for GGUF file")
    parser.add_argument(
        "--base-model",
        default="llama3.2-3b",
        choices=list(MODEL_MAP.keys()),
        help="Base model that was fine-tuned",
    )
    parser.add_argument(
        "--quantization",
        default="q4_k_m",
        choices=QUANT_METHODS,
        help="Quantization method (q4_k_m recommended)",
    )
    parser.add_argument("--max-seq-length", type=int, default=2048)
    args = parser.parse_args()

    model_id = MODEL_MAP[args.base_model]
    print(f"Loading base model {model_id} + adapter from {args.adapter}...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.adapter,
        max_seq_length=args.max_seq_length,
        load_in_4bit=True,
    )

    print(f"Exporting to GGUF with {args.quantization} quantization...")
    print(f"Output: {args.output}/")

    model.save_pretrained_gguf(
        args.output,
        tokenizer,
        quantization_method=args.quantization,
    )

    print(f"\nGGUF export complete!")
    print(f"\nNext steps:")
    print(f"  1. Create a Modelfile (see Modelfile.example in this directory)")
    print(f"  2. Run: ollama create my-pdf-model -f Modelfile")
    print(f"  3. Test: ollama run my-pdf-model")
    print(f"  4. Use in RAG: set OLLAMA_MODEL=my-pdf-model in .env")


if __name__ == "__main__":
    main()
