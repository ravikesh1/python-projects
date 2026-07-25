"""
Fine-tune a model with LoRA on Apple Silicon using MLX.

Usage:
    python train_mlx.py
    python train_mlx.py --base-model mlx-community/Llama-3.2-3B-Instruct-4bit --iters 1000

Requirements: Apple Silicon Mac (M1/M2/M4) with 16GB+ RAM.
"""

import argparse
import subprocess
import sys


MODEL_MAP = {
    "llama3.2-1b": "mlx-community/Llama-3.2-1B-Instruct-4bit",
    "llama3.2-3b": "mlx-community/Llama-3.2-3B-Instruct-4bit",
    "llama3.1-8b": "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
    "mistral-7b": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    "phi-3.5": "mlx-community/Phi-3.5-mini-instruct-4bit",
}

# Rough RAM requirements per model
RAM_NEEDED = {
    "llama3.2-1b": "8GB",
    "llama3.2-3b": "16GB",
    "llama3.1-8b": "24GB",
    "mistral-7b": "24GB",
    "phi-3.5": "16GB",
}


def main():
    parser = argparse.ArgumentParser(description="Fine-tune with MLX on Apple Silicon")
    parser.add_argument("--data-dir", default="data", help="Directory with train/valid/test JSONL")
    parser.add_argument("--base-model", default="llama3.2-3b", choices=list(MODEL_MAP.keys()))
    parser.add_argument("--adapter-path", default="adapters", help="Output adapter directory")
    parser.add_argument("--iters", type=int, default=600, help="Training iterations")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lora-layers", type=int, default=16, help="Number of LoRA layers")
    parser.add_argument("--lr", type=float, default=1e-5, help="Learning rate")
    args = parser.parse_args()

    model_id = MODEL_MAP[args.base_model]
    ram = RAM_NEEDED[args.base_model]

    print(f"Model: {model_id}")
    print(f"Min RAM needed: {ram}")
    print(f"Iterations: {args.iters}")
    print(f"LoRA layers: {args.lora_layers}")
    print(f"Batch size: {args.batch_size}")
    print(f"Learning rate: {args.lr}")
    print()

    cmd = [
        sys.executable, "-m", "mlx_lm.lora",
        "--model", model_id,
        "--data", args.data_dir,
        "--train",
        "--iters", str(args.iters),
        "--batch-size", str(args.batch_size),
        "--lora-layers", str(args.lora_layers),
        "--learning-rate", str(args.lr),
        "--adapter-path", args.adapter_path,
    ]

    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\nTraining complete! Adapter saved to {args.adapter_path}/")
        print(f"Next: python export_mlx.py --base-model {args.base_model}")
    else:
        print(f"\nTraining failed with exit code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
