"""Export a fine-tuned model to GGUF format and create an Ollama model.

This script:
  1. Merges the LoRA adapter back into the base model
  2. Exports to GGUF format (quantized for efficient inference)
  3. Generates an Ollama Modelfile
  4. Optionally creates the Ollama model via `ollama create`

Usage:
    python export_to_ollama.py --model-dir ./output --model-name my-model
    python export_to_ollama.py --model-dir ./output --quantization q8_0 --no-create
"""

import argparse
import subprocess
from pathlib import Path

from unsloth import FastLanguageModel


QUANTIZATION_OPTIONS = {
    "q4_k_m": "Good balance of quality and size (recommended)",
    "q5_k_m": "Higher quality, slightly larger",
    "q8_0": "Near-original quality, larger file",
    "f16": "Full precision, largest file",
    "q2_k": "Smallest size, lower quality",
    "q3_k_m": "Small size, moderate quality",
    "q6_k": "High quality, moderate size",
}


def generate_modelfile(gguf_path: str, system_prompt: str) -> str:
    return f"""FROM {gguf_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 2048
PARAMETER repeat_penalty 1.1

SYSTEM \"\"\"{system_prompt}\"\"\"
"""


def main():
    parser = argparse.ArgumentParser(description="Export fine-tuned model to Ollama")
    parser.add_argument("--model-dir", required=True, help="Directory with the fine-tuned model")
    parser.add_argument("--model-name", default="my-custom-model",
                        help="Name for the Ollama model")
    parser.add_argument("--quantization", default="q4_k_m",
                        choices=list(QUANTIZATION_OPTIONS.keys()),
                        help="GGUF quantization level")
    parser.add_argument("--system-prompt", default="You are a helpful assistant.",
                        help="System prompt for the Ollama model")
    parser.add_argument("--no-create", action="store_true",
                        help="Only export GGUF, don't run ollama create")
    parser.add_argument("--output-dir", help="Directory for GGUF output (default: model-dir)")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir) if args.output_dir else model_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading model from: {model_dir}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(model_dir),
        max_seq_length=2048,
        load_in_4bit=True,
    )

    quant = args.quantization
    gguf_path = output_dir / f"model-{quant}.gguf"

    print(f"Exporting to GGUF ({quant}: {QUANTIZATION_OPTIONS[quant]})...")
    model.save_pretrained_gguf(
        str(output_dir),
        tokenizer,
        quantization_method=quant,
    )

    actual_gguf = None
    for f in output_dir.iterdir():
        if f.suffix == ".gguf":
            actual_gguf = f
            break

    if not actual_gguf:
        print("ERROR: No .gguf file found after export. Check for errors above.")
        return

    print(f"GGUF file: {actual_gguf}")
    size_mb = actual_gguf.stat().st_size / (1024 * 1024)
    print(f"GGUF size: {size_mb:.1f} MB")

    modelfile_content = generate_modelfile(str(actual_gguf.resolve()), args.system_prompt)
    modelfile_path = output_dir / "Modelfile"
    modelfile_path.write_text(modelfile_content)
    print(f"Modelfile written to: {modelfile_path}")

    if args.no_create:
        print(f"\nTo create the Ollama model manually:")
        print(f"  ollama create {args.model_name} -f {modelfile_path}")
        return

    print(f"\nCreating Ollama model: {args.model_name}")
    result = subprocess.run(
        ["ollama", "create", args.model_name, "-f", str(modelfile_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"Model created successfully!")
        print(f"\nRun it with:")
        print(f"  ollama run {args.model_name}")
    else:
        print(f"ollama create failed (is Ollama running?):")
        print(result.stderr)
        print(f"\nYou can create it manually later:")
        print(f"  ollama create {args.model_name} -f {modelfile_path}")


if __name__ == "__main__":
    main()
