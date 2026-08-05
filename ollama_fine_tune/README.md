# Ollama Fine-Tuning Pipeline

Fine-tune open-source LLMs and deploy them locally with Ollama.

## Workflow

1. **Prepare** your training data in JSONL format
2. **Fine-tune** using Unsloth (LoRA/QLoRA) — 2x faster, 60% less memory
3. **Export** to GGUF format
4. **Import** into Ollama via a Modelfile

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Prepare your dataset
python prepare_data.py --input your_data.csv --output data/train.jsonl

# Fine-tune (adjust for your GPU)
python fine_tune.py \
    --model "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit" \
    --dataset data/train.jsonl \
    --epochs 3 \
    --output ./output

# Export to GGUF and create Ollama model
python export_to_ollama.py \
    --model-dir ./output \
    --model-name my-custom-model \
    --quantization q4_k_m
```

## Hardware Requirements

| Model Size | Min VRAM | Recommended |
|-----------|----------|-------------|
| 1B-3B     | 4 GB     | 8 GB        |
| 7B-8B     | 8 GB     | 16 GB       |
| 13B       | 16 GB    | 24 GB       |
| 70B       | 48 GB    | 80 GB       |

CPU-only fine-tuning is possible but very slow — a GPU is strongly recommended.

## Project Structure

```
ollama_fine_tune/
├── fine_tune.py           # Main fine-tuning script (Unsloth + LoRA)
├── prepare_data.py        # Convert CSV/JSON to training format
├── export_to_ollama.py    # Export model to GGUF and create Ollama model
├── config.py              # Training configuration
├── requirements.txt       # Python dependencies
├── data/
│   └── example_train.jsonl  # Example training data
└── Modelfile.template     # Ollama Modelfile template
```
