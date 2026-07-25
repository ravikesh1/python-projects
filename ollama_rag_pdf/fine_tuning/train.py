"""
Step 2: Fine-tune a model with LoRA using Unsloth.

This takes your training JSONL and produces a LoRA adapter that you
can merge into the base model and export to GGUF for Ollama.

Usage:
    python train.py --data data/training.jsonl --output model_output

Requirements:
    - NVIDIA GPU with >= 8GB VRAM (RTX 3060 or better)
    - CUDA installed
    - pip install -r requirements.txt

What this does:
    1. Loads a 4-bit quantized base model (saves GPU memory)
    2. Attaches LoRA adapters to attention layers
    3. Trains on your instruction/response pairs
    4. Saves the LoRA adapter weights
"""

import argparse
import json
import os

from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel


# Maps friendly names to Unsloth model IDs
MODEL_MAP = {
    "llama3.2-1b": "unsloth/Llama-3.2-1B-Instruct-bnb-4bit",
    "llama3.2-3b": "unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
    "llama3.1-8b": "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    "mistral-7b": "unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
    "phi-3.5": "unsloth/Phi-3.5-mini-instruct-bnb-4bit",
}

PROMPT_TEMPLATE = """### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""


def load_training_data(path: str) -> Dataset:
    examples = []
    with open(path) as f:
        for line in f:
            ex = json.loads(line.strip())
            if ex["output"].startswith("<FILL"):
                continue
            examples.append(ex)

    if not examples:
        raise ValueError(
            "No usable training examples found. "
            "All outputs are placeholders — run prepare_data.py with --auto-generate first."
        )

    print(f"Loaded {len(examples)} training examples (skipped placeholders)")
    return Dataset.from_list(examples)


def format_example(example: dict) -> dict:
    """Format a single example into the prompt template."""
    text = PROMPT_TEMPLATE.format(
        instruction=example["instruction"],
        input=example["input"],
        output=example["output"],
    )
    return {"text": text}


def main():
    parser = argparse.ArgumentParser(description="Fine-tune with LoRA via Unsloth")
    parser.add_argument("--data", default="data/training.jsonl", help="Training JSONL file")
    parser.add_argument("--output", default="model_output", help="Output directory for adapter")
    parser.add_argument(
        "--base-model",
        default="llama3.2-3b",
        choices=list(MODEL_MAP.keys()),
        help="Base model to fine-tune",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=2, help="Per-device batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max-seq-length", type=int, default=2048, help="Max sequence length")
    parser.add_argument("--lora-rank", type=int, default=16, help="LoRA rank (r)")
    parser.add_argument("--lora-alpha", type=int, default=16, help="LoRA alpha scaling")
    args = parser.parse_args()

    # --- 1. Load base model in 4-bit ---
    model_id = MODEL_MAP[args.base_model]
    print(f"Loading {model_id}...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_id,
        max_seq_length=args.max_seq_length,
        load_in_4bit=True,
    )

    # --- 2. Attach LoRA adapters ---
    #
    # r (rank): Controls adapter capacity. 16 is a good default.
    #   - Lower (8): faster training, less capacity
    #   - Higher (32-64): more capacity, more memory, risk of overfitting
    #
    # target_modules: Which layers get adapters.
    #   - q_proj, k_proj: what to attend to (query and key)
    #   - v_proj, o_proj: what information to extract and output
    #   - gate_proj, up_proj, down_proj: the feed-forward network
    #
    # More modules = more expressive but slower and more memory.
    # Start with just attention (q/k/v/o), add FFN modules if underfitting.

    print(f"Attaching LoRA adapters (rank={args.lora_rank}, alpha={args.lora_alpha})...")

    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=0,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"Trainable parameters: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

    # --- 3. Load and format training data ---
    dataset = load_training_data(args.data)
    dataset = dataset.map(format_example)

    # --- 4. Train ---
    print(f"\nStarting training for {args.epochs} epochs...")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=4,
            num_train_epochs=args.epochs,
            learning_rate=args.lr,
            lr_scheduler_type="linear",
            warmup_steps=5,
            weight_decay=0.01,
            logging_steps=1,
            output_dir=args.output,
            save_strategy="epoch",
            fp16=True,
            optim="adamw_8bit",
            seed=42,
        ),
    )

    stats = trainer.train()

    print(f"\nTraining complete!")
    print(f"  Total steps: {stats.global_step}")
    print(f"  Final loss: {stats.training_loss:.4f}")

    # --- 5. Save adapter ---
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    print(f"Adapter saved to {args.output}/")


if __name__ == "__main__":
    main()
