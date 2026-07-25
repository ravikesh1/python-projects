"""
Step 2: Fine-tune with LoRA using Unsloth.

Takes your training JSONL and produces a LoRA adapter.

Usage:
    python train.py --data data/training.jsonl
    python train.py --data data/training.jsonl --base-model llama3.1-8b --epochs 5 --lora-rank 32

Requirements: NVIDIA GPU with >= 8GB VRAM, CUDA installed.
"""

import argparse
import json

from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel


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


def load_data(path: str) -> Dataset:
    examples = []
    with open(path) as f:
        for line in f:
            ex = json.loads(line.strip())
            if ex["output"].startswith("<FILL"):
                continue
            examples.append(ex)

    if not examples:
        raise ValueError("No usable examples — all outputs are placeholders")

    print(f"Loaded {len(examples)} training examples")
    return Dataset.from_list(examples)


def format_example(example: dict) -> dict:
    return {"text": PROMPT_TEMPLATE.format(**example)}


def main():
    parser = argparse.ArgumentParser(description="Fine-tune with LoRA")
    parser.add_argument("--data", default="data/training.jsonl")
    parser.add_argument("--output", default="model_output")
    parser.add_argument("--base-model", default="llama3.2-3b", choices=list(MODEL_MAP.keys()))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-seq-length", type=int, default=2048)
    parser.add_argument("--lora-rank", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=16)
    args = parser.parse_args()

    # 1. Load base model in 4-bit (QLoRA)
    model_id = MODEL_MAP[args.base_model]
    print(f"Loading {model_id}...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_id,
        max_seq_length=args.max_seq_length,
        load_in_4bit=True,
    )

    # 2. Attach LoRA adapters
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
    print(f"Trainable: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)")

    # 3. Load data
    dataset = load_data(args.data)
    dataset = dataset.map(format_example)

    # 4. Train
    print(f"\nTraining for {args.epochs} epochs...")

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
    print(f"\nDone! Loss: {stats.training_loss:.4f}, Steps: {stats.global_step}")

    # 5. Save
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    print(f"Adapter saved to {args.output}/")


if __name__ == "__main__":
    main()
