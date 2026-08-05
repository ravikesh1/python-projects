"""Fine-tune an LLM using Unsloth + LoRA, then save the adapter.

Unsloth provides 2x faster training and 60% less memory than standard
HuggingFace training. It patches the model in-place for speed.

Usage:
    python fine_tune.py
    python fine_tune.py --model "unsloth/Llama-3.2-3B-Instruct-bnb-4bit" --epochs 5
    python fine_tune.py --model-alias llama-3.1-8b --dataset data/train.jsonl
"""

import argparse
import json
from pathlib import Path

from datasets import Dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import FastLanguageModel

from config import ModelConfig, SUPPORTED_MODELS


def load_dataset_from_jsonl(path: str) -> Dataset:
    conversations = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                conversations.append(json.loads(line))
    return Dataset.from_dict({"conversations": conversations})


def format_conversation(example: dict, tokenizer) -> dict:
    return {"text": tokenizer.apply_chat_template(
        example["conversations"],
        tokenize=False,
        add_generation_prompt=False,
    )}


def main():
    parser = argparse.ArgumentParser(description="Fine-tune a model with Unsloth + LoRA")
    parser.add_argument("--model", help="HuggingFace model ID or Unsloth quantized model")
    parser.add_argument("--model-alias", choices=list(SUPPORTED_MODELS.keys()),
                        help="Use a preset model alias")
    parser.add_argument("--dataset", help="Path to training JSONL")
    parser.add_argument("--epochs", type=int, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, help="Per-device batch size")
    parser.add_argument("--lr", type=float, help="Learning rate")
    parser.add_argument("--lora-r", type=int, help="LoRA rank")
    parser.add_argument("--max-seq-length", type=int, help="Max sequence length")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--resume", help="Resume from checkpoint directory")
    args = parser.parse_args()

    cfg = ModelConfig()
    if args.model_alias:
        cfg.model_name = SUPPORTED_MODELS[args.model_alias]
    if args.model:
        cfg.model_name = args.model
    if args.dataset:
        cfg.dataset_path = args.dataset
    if args.epochs:
        cfg.num_train_epochs = args.epochs
    if args.batch_size:
        cfg.per_device_train_batch_size = args.batch_size
    if args.lr:
        cfg.learning_rate = args.lr
    if args.lora_r:
        cfg.lora_r = args.lora_r
    if args.max_seq_length:
        cfg.max_seq_length = args.max_seq_length
    if args.output:
        cfg.output_dir = args.output

    print(f"Loading model: {cfg.model_name}")
    print(f"Max sequence length: {cfg.max_seq_length}")
    print(f"4-bit quantization: {cfg.load_in_4bit}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=cfg.model_name,
        max_seq_length=cfg.max_seq_length,
        load_in_4bit=cfg.load_in_4bit,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        lora_dropout=cfg.lora_dropout,
        target_modules=cfg.target_modules,
        use_gradient_checkpointing="unsloth",
    )

    trainable, total = model.get_nb_trainable_parameters()
    print(f"Trainable parameters: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)")

    print(f"Loading dataset: {cfg.dataset_path}")
    dataset = load_dataset_from_jsonl(cfg.dataset_path)
    dataset = dataset.map(lambda ex: format_conversation(ex, tokenizer))
    print(f"Training examples: {len(dataset)}")

    training_args = TrainingArguments(
        output_dir=cfg.output_dir,
        num_train_epochs=cfg.num_train_epochs,
        per_device_train_batch_size=cfg.per_device_train_batch_size,
        gradient_accumulation_steps=cfg.gradient_accumulation_steps,
        learning_rate=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
        warmup_steps=cfg.warmup_steps,
        lr_scheduler_type=cfg.lr_scheduler_type,
        fp16=cfg.fp16,
        bf16=cfg.bf16,
        logging_steps=cfg.logging_steps,
        save_steps=cfg.save_steps,
        save_total_limit=3,
        seed=cfg.seed,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        dataset_text_field="text",
        max_seq_length=cfg.max_seq_length,
        packing=False,
    )

    print("Starting training...")
    trainer.train(resume_from_checkpoint=args.resume)

    print(f"Saving model to {cfg.output_dir}")
    model.save_pretrained(cfg.output_dir)
    tokenizer.save_pretrained(cfg.output_dir)

    print("Training complete!")
    print(f"Model saved to: {cfg.output_dir}")
    print(f"Next step: python export_to_ollama.py --model-dir {cfg.output_dir}")


if __name__ == "__main__":
    main()
