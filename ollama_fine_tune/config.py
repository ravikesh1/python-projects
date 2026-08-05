from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    model_name: str = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"
    max_seq_length: int = 2048
    load_in_4bit: bool = True

    # LoRA parameters
    lora_r: int = 16
    lora_alpha: int = 16
    lora_dropout: float = 0.0
    target_modules: list[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

    # Training parameters
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_steps: int = 5
    lr_scheduler_type: str = "linear"
    fp16: bool = False
    bf16: bool = True
    logging_steps: int = 10
    save_steps: int = 100
    seed: int = 42

    output_dir: str = "./output"
    dataset_path: str = "data/train.jsonl"


SUPPORTED_MODELS = {
    "llama-3.1-8b": "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    "llama-3.2-3b": "unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
    "llama-3.2-1b": "unsloth/Llama-3.2-1B-Instruct-bnb-4bit",
    "mistral-7b": "unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
    "gemma-2-9b": "unsloth/gemma-2-9b-it-bnb-4bit",
    "gemma-2-2b": "unsloth/gemma-2-2b-it-bnb-4bit",
    "phi-3.5-mini": "unsloth/Phi-3.5-mini-instruct-bnb-4bit",
    "qwen-2.5-7b": "unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
    "qwen-2.5-3b": "unsloth/Qwen2.5-3B-Instruct-bnb-4bit",
}
