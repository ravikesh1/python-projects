"""
Fuse LoRA adapter into base model and convert to GGUF for Ollama.

Usage:
    python export_mlx.py
    python export_mlx.py --base-model llama3.1-8b --quantization q5_k_m

Then:
    ollama create my-model -f Modelfile
    ollama run my-model
"""

import argparse
import subprocess
import sys
import os


MODEL_MAP = {
    "llama3.2-1b": "mlx-community/Llama-3.2-1B-Instruct-4bit",
    "llama3.2-3b": "mlx-community/Llama-3.2-3B-Instruct-4bit",
    "llama3.1-8b": "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
    "mistral-7b": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    "phi-3.5": "mlx-community/Phi-3.5-mini-instruct-4bit",
}


def run_cmd(cmd: list[str], description: str):
    print(f"\n{description}...")
    print(f"  {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  Failed with exit code {result.returncode}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Export MLX model to GGUF for Ollama")
    parser.add_argument("--adapter-path", default="adapters")
    parser.add_argument("--base-model", default="llama3.2-3b", choices=list(MODEL_MAP.keys()))
    parser.add_argument("--fused-path", default="fused_model", help="Fused model output")
    parser.add_argument("--gguf-path", default="model.gguf", help="GGUF output file")
    args = parser.parse_args()

    model_id = MODEL_MAP[args.base_model]

    # Step 1: Fuse adapter into base model
    run_cmd(
        [
            sys.executable, "-m", "mlx_lm.fuse",
            "--model", model_id,
            "--adapter-path", args.adapter_path,
            "--save-path", args.fused_path,
        ],
        "Fusing LoRA adapter into base model",
    )

    # Step 2: Convert to GGUF
    run_cmd(
        [
            sys.executable, "-m", "mlx_lm.convert",
            "--model", args.fused_path,
            "--to-gguf",
            "-o", args.gguf_path,
        ],
        "Converting to GGUF format",
    )

    print(f"\nDone! GGUF saved to {args.gguf_path}")
    print(f"\nNext steps:")
    print(f"  1. Update Modelfile: FROM ./{args.gguf_path}")
    print(f"  2. ollama create my-model -f Modelfile")
    print(f"  3. ollama run my-model")


if __name__ == "__main__":
    main()
