"""Generate the 'Complete Guide: Fine-Tuning LLMs for Ollama' PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Preformatted, KeepTogether, HRFlowable,
)


BLUE = HexColor("#1a56db")
DARK = HexColor("#1e293b")
GRAY = HexColor("#475569")
LIGHT_BG = HexColor("#f1f5f9")
CODE_BG = HexColor("#f8fafc")
WHITE = HexColor("#ffffff")
GREEN = HexColor("#15803d")
ORANGE = HexColor("#c2410c")


def build_styles():
    ss = getSampleStyleSheet()

    ss.add(ParagraphStyle(
        "CoverTitle", parent=ss["Title"], fontSize=28, leading=34,
        textColor=DARK, alignment=TA_CENTER, spaceAfter=12,
    ))
    ss.add(ParagraphStyle(
        "CoverSubtitle", parent=ss["Normal"], fontSize=14, leading=18,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=6,
    ))
    ss.add(ParagraphStyle(
        "SectionHead", parent=ss["Heading1"], fontSize=20, leading=26,
        textColor=BLUE, spaceBefore=24, spaceAfter=10,
        borderColor=BLUE, borderWidth=0, borderPadding=0,
    ))
    ss.add(ParagraphStyle(
        "SubHead", parent=ss["Heading2"], fontSize=15, leading=20,
        textColor=DARK, spaceBefore=16, spaceAfter=8,
    ))
    ss.add(ParagraphStyle(
        "SubSubHead", parent=ss["Heading3"], fontSize=12, leading=16,
        textColor=GRAY, spaceBefore=12, spaceAfter=6,
    ))
    ss.add(ParagraphStyle(
        "Body", parent=ss["Normal"], fontSize=10, leading=14,
        textColor=DARK, spaceAfter=8,
    ))
    ss.add(ParagraphStyle(
        "BulletItem", parent=ss["Normal"], fontSize=10, leading=14,
        textColor=DARK, leftIndent=20, bulletIndent=8, spaceAfter=4,
    ))
    ss.add(ParagraphStyle(
        "CodeBlock", fontName="Courier", fontSize=8.5, leading=12,
        textColor=DARK, backColor=CODE_BG, leftIndent=12, rightIndent=12,
        spaceBefore=6, spaceAfter=10, borderColor=HexColor("#e2e8f0"),
        borderWidth=0.5, borderPadding=8, borderRadius=4,
    ))
    ss.add(ParagraphStyle(
        "Note", parent=ss["Normal"], fontSize=9.5, leading=13,
        textColor=ORANGE, leftIndent=16, rightIndent=16,
        spaceBefore=6, spaceAfter=10, backColor=HexColor("#fff7ed"),
        borderColor=ORANGE, borderWidth=0.5, borderPadding=8,
    ))
    ss.add(ParagraphStyle(
        "Tip", parent=ss["Normal"], fontSize=9.5, leading=13,
        textColor=GREEN, leftIndent=16, rightIndent=16,
        spaceBefore=6, spaceAfter=10, backColor=HexColor("#f0fdf4"),
        borderColor=GREEN, borderWidth=0.5, borderPadding=8,
    ))
    return ss


def code(text, styles):
    escaped = (text
               .replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;"))
    return Preformatted(escaped, styles["CodeBlock"])


def bullet(text, styles):
    return Paragraph(f"&bull;  {text}", styles["BulletItem"])


def add_cover(story, styles):
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("Complete Guide", styles["CoverTitle"]))
    story.append(Paragraph("Fine-Tuning LLMs for Ollama", styles["CoverTitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Using Unsloth + LoRA for Fast, Memory-Efficient Training", styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("From raw data to a running Ollama model in 3 steps", styles["CoverSubtitle"]))
    story.append(Spacer(1, 1.5 * inch))
    story.append(HRFlowable(width="60%", color=BLUE, thickness=2, spaceAfter=12))
    story.append(Paragraph("Step-by-step instructions with complete code", styles["CoverSubtitle"]))
    story.append(PageBreak())


def add_toc(story, styles):
    story.append(Paragraph("Table of Contents", styles["SectionHead"]))
    story.append(Spacer(1, 0.1 * inch))
    toc_items = [
        "1.  Overview &amp; Architecture",
        "2.  Prerequisites &amp; Installation",
        "3.  Step 1: Prepare Your Training Data",
        "4.  Step 2: Fine-Tune with Unsloth + LoRA",
        "5.  Step 3: Export to GGUF &amp; Deploy to Ollama",
        "6.  Complete Configuration Reference",
        "7.  Supported Models",
        "8.  Troubleshooting &amp; Tips",
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles["Body"]))
    story.append(PageBreak())


def add_overview(story, styles):
    story.append(Paragraph("1.  Overview &amp; Architecture", styles["SectionHead"]))
    story.append(Paragraph(
        "Ollama does not support fine-tuning directly. The workflow is to fine-tune a base "
        "model using Python tools, convert it to GGUF format, and import it into Ollama.",
        styles["Body"],
    ))
    story.append(Paragraph("The Pipeline", styles["SubHead"]))

    pipeline_data = [
        ["Stage", "Tool", "What It Does"],
        ["1. Data Prep", "prepare_data.py", "Converts CSV/JSON to chat-format JSONL"],
        ["2. Fine-Tune", "fine_tune.py\n(Unsloth + LoRA)", "Trains a LoRA adapter on your data\n2x faster, 60% less VRAM"],
        ["3. Export", "export_to_ollama.py", "Merges adapter, exports GGUF,\ncreates Ollama model"],
    ]
    t = Table(pipeline_data, colWidths=[1.2 * inch, 1.8 * inch, 3 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 13),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Why Unsloth + LoRA?", styles["SubHead"]))
    story.append(bullet("LoRA trains only ~1-2% of model parameters, so it needs far less memory", styles))
    story.append(bullet("Unsloth optimizes the training loop for 2x speed on the same hardware", styles))
    story.append(bullet("A 7-8B model can be fine-tuned on a single 16 GB GPU (or even 8 GB with 4-bit)", styles))
    story.append(bullet("The result is identical to full fine-tuning for most use cases", styles))
    story.append(PageBreak())


def add_prerequisites(story, styles):
    story.append(Paragraph("2.  Prerequisites &amp; Installation", styles["SectionHead"]))

    story.append(Paragraph("Hardware Requirements", styles["SubHead"]))
    hw_data = [
        ["Model Size", "Min VRAM", "Recommended", "Example GPUs"],
        ["1B - 3B", "4 GB", "8 GB", "RTX 3060, T4"],
        ["7B - 8B", "8 GB", "16 GB", "RTX 4070, A10"],
        ["13B", "16 GB", "24 GB", "RTX 4090, A5000"],
        ["70B", "48 GB", "80 GB", "A100, H100"],
    ]
    t = Table(hw_data, colWidths=[1.2 * inch, 1 * inch, 1.2 * inch, 2.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Software Requirements", styles["SubHead"]))
    story.append(bullet("Python 3.10+", styles))
    story.append(bullet("CUDA 11.8+ (for GPU training)", styles))
    story.append(bullet("Ollama installed locally (for deployment)", styles))

    story.append(Paragraph("Installation", styles["SubHead"]))
    story.append(Paragraph("Install all dependencies:", styles["Body"]))
    story.append(code(
        "pip install -r requirements.txt",
        styles,
    ))

    story.append(Paragraph("Or install individually:", styles["Body"]))
    story.append(code(
        'pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"\n'
        "pip install torch transformers datasets trl peft accelerate\n"
        "pip install bitsandbytes xformers sentencepiece",
        styles,
    ))

    story.append(Paragraph("Install Ollama:", styles["Body"]))
    story.append(code("curl -fsSL https://ollama.ai/install.sh | sh", styles))

    story.append(Paragraph(
        "Note: On Google Colab (free tier with T4 GPU), Unsloth works out of the box. "
        "This is the easiest way to get started if you don't have a local GPU.",
        styles["Note"],
    ))
    story.append(PageBreak())


def add_step1_data(story, styles):
    story.append(Paragraph("3.  Step 1: Prepare Your Training Data", styles["SectionHead"]))

    story.append(Paragraph(
        "Fine-tuning requires training data in chat format. Each example is a conversation "
        "with system, user, and assistant messages.",
        styles["Body"],
    ))

    story.append(Paragraph("Option A: Start from CSV", styles["SubHead"]))
    story.append(Paragraph("Create a CSV file with these columns:", styles["Body"]))
    story.append(code(
        "instruction,input,output\n"
        '"Explain what a REST API is","","A REST API is an architectural style..."\n'
        '"Convert this to Python","for(int i=0;i<10;i++)","for i in range(10):..."\n'
        '"Summarize this text","Long article here...","Brief summary here..."',
        styles,
    ))

    story.append(Paragraph("Then convert it:", styles["Body"]))
    story.append(code(
        "python prepare_data.py \\\n"
        "    --input your_data.csv \\\n"
        "    --output data/train.jsonl \\\n"
        '    --system-prompt "You are a helpful coding assistant."',
        styles,
    ))

    story.append(Paragraph("Option B: Write JSONL Directly (Recommended)", styles["SubHead"]))
    story.append(Paragraph("Each line is a JSON array of chat messages:", styles["Body"]))
    story.append(code(
        '[\n'
        '  {"role": "system", "content": "You are a helpful assistant."},\n'
        '  {"role": "user", "content": "How do I read a CSV in Python?"},\n'
        '  {"role": "assistant", "content": "Use pandas:\\n```python\\n'
        "import pandas as pd\\ndf = pd.read_csv('data.csv')\\n```\"}\n"
        ']',
        styles,
    ))

    story.append(Paragraph(
        "Tip: Aim for 100-1000+ examples for good results. Quality matters more than "
        "quantity. Each example should demonstrate the exact behavior you want.",
        styles["Tip"],
    ))

    story.append(Paragraph("Option C: Start from JSON", styles["SubHead"]))
    story.append(code(
        '[\n'
        '  {"instruction": "Explain decorators", "output": "Decorators wrap..."},\n'
        '  {"instruction": "Fix this code", "input": "buggy code", "output": "fixed"}\n'
        ']',
        styles,
    ))

    story.append(Paragraph("The prepare_data.py Script (Complete Code)", styles["SubHead"]))
    story.append(code(
        '"""Convert raw data into chat format for fine-tuning."""\n'
        "\n"
        "import argparse\n"
        "import csv\n"
        "import json\n"
        "from pathlib import Path\n"
        "\n"
        "\n"
        "def convert_row_to_chat(row: dict, system_prompt: str) -> list[dict]:\n"
        '    user_content = row["instruction"]\n'
        '    if row.get("input"):\n'
        "        user_content += f\"\\n\\n{row['input']}\"\n"
        "\n"
        "    messages = []\n"
        "    if system_prompt:\n"
        '        messages.append({"role": "system", "content": system_prompt})\n'
        '    messages.append({"role": "user", "content": user_content})\n'
        '    messages.append({"role": "assistant", "content": row["output"]})\n'
        "    return messages\n"
        "\n"
        "\n"
        "def load_csv(path: Path) -> list[dict]:\n"
        '    with open(path, newline="", encoding="utf-8") as f:\n'
        "        return list(csv.DictReader(f))\n"
        "\n"
        "\n"
        "def load_json(path: Path) -> list[dict]:\n"
        '    with open(path, encoding="utf-8") as f:\n'
        "        data = json.load(f)\n"
        "    return data if isinstance(data, list) else [data]\n"
        "\n"
        "\n"
        "def load_jsonl(path: Path) -> list[dict]:\n"
        "    rows = []\n"
        '    with open(path, encoding="utf-8") as f:\n'
        "        for line in f:\n"
        "            line = line.strip()\n"
        "            if line:\n"
        "                rows.append(json.loads(line))\n"
        "    return rows\n"
        "\n"
        "\n"
        "def main():\n"
        "    parser = argparse.ArgumentParser()\n"
        '    parser.add_argument("--input", required=True)\n'
        '    parser.add_argument("--output", default="data/train.jsonl")\n'
        '    parser.add_argument("--system-prompt",\n'
        '                        default="You are a helpful assistant.")\n'
        "    args = parser.parse_args()\n"
        "\n"
        "    input_path = Path(args.input)\n"
        "    suffix = input_path.suffix.lower()\n"
        "    loaders = {\n"
        '        ".csv": load_csv, ".json": load_json, ".jsonl": load_jsonl\n'
        "    }\n"
        "    rows = loaders[suffix](input_path)\n"
        "\n"
        "    conversations = []\n"
        "    for row in rows:\n"
        "        # Already in chat format\n"
        "        if isinstance(row, list):\n"
        "            conversations.append(row)\n"
        '        elif "messages" in row:\n'
        '            conversations.append(row["messages"])\n'
        "        else:\n"
        "            conversations.append(\n"
        "                convert_row_to_chat(row, args.system_prompt)\n"
        "            )\n"
        "\n"
        "    output_path = Path(args.output)\n"
        "    output_path.parent.mkdir(parents=True, exist_ok=True)\n"
        '    with open(output_path, "w", encoding="utf-8") as f:\n'
        "        for conv in conversations:\n"
        "            f.write(json.dumps(conv, ensure_ascii=False) + \"\\n\")\n"
        "\n"
        '    print(f"Wrote {len(conversations)} examples to {output_path}")\n'
        "\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    main()",
        styles,
    ))
    story.append(PageBreak())


def add_step2_finetune(story, styles):
    story.append(Paragraph("4.  Step 2: Fine-Tune with Unsloth + LoRA", styles["SectionHead"]))

    story.append(Paragraph("Quick Start Command", styles["SubHead"]))
    story.append(code(
        "python fine_tune.py \\\n"
        '    --model "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit" \\\n'
        "    --dataset data/train.jsonl \\\n"
        "    --epochs 3 \\\n"
        "    --output ./output",
        styles,
    ))

    story.append(Paragraph("Or use a model alias:", styles["Body"]))
    story.append(code(
        "python fine_tune.py \\\n"
        "    --model-alias llama-3.1-8b \\\n"
        "    --dataset data/train.jsonl \\\n"
        "    --epochs 3",
        styles,
    ))

    story.append(Paragraph("Understanding the Training Script", styles["SubHead"]))
    story.append(Paragraph("The fine-tuning script does four things:", styles["Body"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1. Load the base model (4-bit quantized for memory efficiency)", styles["SubSubHead"]))
    story.append(code(
        "from unsloth import FastLanguageModel\n"
        "\n"
        "model, tokenizer = FastLanguageModel.from_pretrained(\n"
        '    model_name="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",\n'
        "    max_seq_length=2048,\n"
        "    load_in_4bit=True,\n"
        ")",
        styles,
    ))

    story.append(Paragraph("2. Add LoRA adapters (train only 1-2% of parameters)", styles["SubSubHead"]))
    story.append(code(
        "model = FastLanguageModel.get_peft_model(\n"
        "    model,\n"
        "    r=16,              # LoRA rank: higher = more capacity\n"
        "    lora_alpha=16,     # Scaling factor\n"
        "    lora_dropout=0.0,  # No dropout for Unsloth\n"
        "    target_modules=[\n"
        '        "q_proj", "k_proj", "v_proj", "o_proj",\n'
        '        "gate_proj", "up_proj", "down_proj",\n'
        "    ],\n"
        '    use_gradient_checkpointing="unsloth",  # 60% less VRAM\n'
        ")",
        styles,
    ))

    story.append(Paragraph("3. Load and format the dataset", styles["SubSubHead"]))
    story.append(code(
        "from datasets import Dataset\n"
        "import json\n"
        "\n"
        "# Load JSONL conversations\n"
        "conversations = []\n"
        'with open("data/train.jsonl") as f:\n'
        "    for line in f:\n"
        "        conversations.append(json.loads(line.strip()))\n"
        "\n"
        'dataset = Dataset.from_dict({"conversations": conversations})\n'
        "\n"
        "# Format using the model's chat template\n"
        "def format_conversation(example):\n"
        '    return {"text": tokenizer.apply_chat_template(\n'
        '        example["conversations"],\n'
        "        tokenize=False,\n"
        "        add_generation_prompt=False,\n"
        "    )}\n"
        "\n"
        "dataset = dataset.map(format_conversation)",
        styles,
    ))

    story.append(Paragraph("4. Train with SFTTrainer", styles["SubSubHead"]))
    story.append(code(
        "from trl import SFTTrainer\n"
        "from transformers import TrainingArguments\n"
        "\n"
        "trainer = SFTTrainer(\n"
        "    model=model,\n"
        "    tokenizer=tokenizer,\n"
        "    train_dataset=dataset,\n"
        "    args=TrainingArguments(\n"
        '        output_dir="./output",\n'
        "        num_train_epochs=3,\n"
        "        per_device_train_batch_size=2,\n"
        "        gradient_accumulation_steps=4,\n"
        "        learning_rate=2e-4,\n"
        "        weight_decay=0.01,\n"
        "        warmup_steps=5,\n"
        '        lr_scheduler_type="linear",\n'
        "        bf16=True,\n"
        "        logging_steps=10,\n"
        "        save_steps=100,\n"
        '        report_to="none",\n'
        "    ),\n"
        '    dataset_text_field="text",\n'
        "    max_seq_length=2048,\n"
        ")\n"
        "\n"
        "trainer.train()\n"
        "\n"
        "# Save the fine-tuned adapter\n"
        'model.save_pretrained("./output")\n'
        'tokenizer.save_pretrained("./output")',
        styles,
    ))

    story.append(Paragraph(
        "Tip: Start with 3 epochs. If the model overfits (training loss drops to ~0 but "
        "output quality is bad), reduce to 1-2 epochs. If quality is poor, add more data "
        "or increase epochs to 5.",
        styles["Tip"],
    ))
    story.append(PageBreak())


def add_step3_export(story, styles):
    story.append(Paragraph("5.  Step 3: Export to GGUF &amp; Deploy to Ollama", styles["SectionHead"]))

    story.append(Paragraph("Quick Start Command", styles["SubHead"]))
    story.append(code(
        "python export_to_ollama.py \\\n"
        "    --model-dir ./output \\\n"
        "    --model-name my-custom-model \\\n"
        "    --quantization q4_k_m",
        styles,
    ))

    story.append(Paragraph("Quantization Options", styles["SubHead"]))
    quant_data = [
        ["Quantization", "Quality", "Size", "Speed", "Use Case"],
        ["q2_k", "Low", "Smallest", "Fastest", "Experimentation only"],
        ["q3_k_m", "Moderate", "Small", "Fast", "Edge devices"],
        ["q4_k_m", "Good", "Medium", "Good", "Recommended default"],
        ["q5_k_m", "High", "Medium-Large", "Good", "Quality-sensitive tasks"],
        ["q6_k", "Very High", "Large", "Moderate", "Near-original quality"],
        ["q8_0", "Near-Original", "Large", "Moderate", "Maximum quality"],
        ["f16", "Original", "Largest", "Slowest", "Benchmarking only"],
    ]
    t = Table(quant_data, colWidths=[1 * inch, 1 * inch, 1.1 * inch, 0.9 * inch, 1.9 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("BACKGROUND", (0, 3), (-1, 3), HexColor("#e0f2fe")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Export Code Explained", styles["SubHead"]))
    story.append(code(
        "from unsloth import FastLanguageModel\n"
        "\n"
        "# 1. Load the fine-tuned model\n"
        "model, tokenizer = FastLanguageModel.from_pretrained(\n"
        '    model_name="./output",\n'
        "    max_seq_length=2048,\n"
        "    load_in_4bit=True,\n"
        ")\n"
        "\n"
        "# 2. Export to GGUF (merges LoRA + quantizes)\n"
        "model.save_pretrained_gguf(\n"
        '    "./output",\n'
        "    tokenizer,\n"
        '    quantization_method="q4_k_m",\n'
        ")",
        styles,
    ))

    story.append(Paragraph("Create the Ollama Modelfile", styles["SubHead"]))
    story.append(code(
        "# Modelfile\n"
        "FROM ./output/model-q4_k_m.gguf\n"
        "\n"
        "PARAMETER temperature 0.7\n"
        "PARAMETER top_p 0.9\n"
        "PARAMETER top_k 40\n"
        "PARAMETER num_ctx 2048\n"
        "PARAMETER repeat_penalty 1.1\n"
        "\n"
        'SYSTEM """You are a helpful coding assistant\n'
        'specialized in Python and data science."""',
        styles,
    ))

    story.append(Paragraph("Create and Run the Model", styles["SubHead"]))
    story.append(code(
        "# Create the Ollama model\n"
        "ollama create my-custom-model -f Modelfile\n"
        "\n"
        "# Run it\n"
        "ollama run my-custom-model\n"
        "\n"
        "# Test with a prompt\n"
        'ollama run my-custom-model "How do I read a CSV in Python?"',
        styles,
    ))

    story.append(Paragraph("Use from Python", styles["SubHead"]))
    story.append(code(
        "import requests\n"
        "import json\n"
        "\n"
        "response = requests.post(\n"
        '    "http://localhost:11434/api/chat",\n'
        "    json={\n"
        '        "model": "my-custom-model",\n'
        '        "messages": [\n'
        '            {"role": "user", "content": "Explain decorators"}\n'
        "        ],\n"
        '        "stream": False,\n'
        "    },\n"
        ")\n"
        "\n"
        'print(response.json()["message"]["content"])',
        styles,
    ))
    story.append(PageBreak())


def add_config_reference(story, styles):
    story.append(Paragraph("6.  Complete Configuration Reference", styles["SectionHead"]))

    story.append(Paragraph("config.py - All Training Parameters", styles["SubHead"]))
    story.append(code(
        "from dataclasses import dataclass, field\n"
        "\n"
        "@dataclass\n"
        "class ModelConfig:\n"
        "    # Model selection\n"
        '    model_name: str = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"\n'
        "    max_seq_length: int = 2048\n"
        "    load_in_4bit: bool = True\n"
        "\n"
        "    # LoRA parameters\n"
        "    lora_r: int = 16         # Rank: 8, 16, 32, 64\n"
        "    lora_alpha: int = 16     # Usually same as r\n"
        "    lora_dropout: float = 0.0\n"
        "    target_modules: list[str] = field(default_factory=lambda: [\n"
        '        "q_proj", "k_proj", "v_proj", "o_proj",\n'
        '        "gate_proj", "up_proj", "down_proj",\n'
        "    ])\n"
        "\n"
        "    # Training parameters\n"
        "    num_train_epochs: int = 3\n"
        "    per_device_train_batch_size: int = 2\n"
        "    gradient_accumulation_steps: int = 4  # Effective batch = 2*4 = 8\n"
        "    learning_rate: float = 2e-4\n"
        "    weight_decay: float = 0.01\n"
        "    warmup_steps: int = 5\n"
        '    lr_scheduler_type: str = "linear"\n'
        "    bf16: bool = True         # Use bfloat16 (Ampere+)\n"
        "    logging_steps: int = 10\n"
        "    save_steps: int = 100\n"
        "    seed: int = 42\n"
        "\n"
        '    output_dir: str = "./output"\n'
        '    dataset_path: str = "data/train.jsonl"',
        styles,
    ))

    story.append(Paragraph("Key Parameters to Tune", styles["SubHead"]))

    params_data = [
        ["Parameter", "Default", "When to Change"],
        ["lora_r", "16", "Increase to 32/64 for complex tasks;\ndecrease to 8 for simple tasks"],
        ["num_train_epochs", "3", "Increase if underfitting;\ndecrease if overfitting"],
        ["learning_rate", "2e-4", "Lower (1e-4) for larger datasets;\nhigher (5e-4) for small datasets"],
        ["batch_size", "2", "Increase if you have more VRAM;\ndecrease if OOM errors"],
        ["max_seq_length", "2048", "Increase for long-form content;\ndecrease to save memory"],
    ]
    t = Table(params_data, colWidths=[1.3 * inch, 0.9 * inch, 3.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 13),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(PageBreak())


def add_supported_models(story, styles):
    story.append(Paragraph("7.  Supported Models", styles["SectionHead"]))

    story.append(Paragraph(
        "These pre-quantized 4-bit models work out of the box with the pipeline. "
        "They download automatically from HuggingFace on first use.",
        styles["Body"],
    ))

    models_data = [
        ["Alias", "HuggingFace ID", "Size", "Best For"],
        ["llama-3.1-8b", "unsloth/Meta-Llama-3.1-8B-\nInstruct-bnb-4bit", "8B", "General purpose,\ncoding, reasoning"],
        ["llama-3.2-3b", "unsloth/Llama-3.2-3B-\nInstruct-bnb-4bit", "3B", "Fast inference,\nedge deployment"],
        ["llama-3.2-1b", "unsloth/Llama-3.2-1B-\nInstruct-bnb-4bit", "1B", "Ultra-fast,\nembedded devices"],
        ["mistral-7b", "unsloth/mistral-7b-\ninstruct-v0.3-bnb-4bit", "7B", "Strong general\nperformance"],
        ["gemma-2-9b", "unsloth/gemma-2-9b-it-\nbnb-4bit", "9B", "Multilingual,\nlong context"],
        ["gemma-2-2b", "unsloth/gemma-2-2b-it-\nbnb-4bit", "2B", "Lightweight,\nfast training"],
        ["phi-3.5-mini", "unsloth/Phi-3.5-mini-\ninstruct-bnb-4bit", "3.8B", "Reasoning,\nmath, code"],
        ["qwen-2.5-7b", "unsloth/Qwen2.5-7B-\nInstruct-bnb-4bit", "7B", "Multilingual,\nChinese + English"],
        ["qwen-2.5-3b", "unsloth/Qwen2.5-3B-\nInstruct-bnb-4bit", "3B", "Compact\nmultilingual"],
    ]
    t = Table(models_data, colWidths=[1.1 * inch, 2.2 * inch, 0.5 * inch, 1.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 12),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Usage with alias:", styles["Body"]))
    story.append(code(
        "python fine_tune.py --model-alias llama-3.2-3b --dataset data/train.jsonl",
        styles,
    ))

    story.append(Paragraph("Usage with any HuggingFace model:", styles["Body"]))
    story.append(code(
        'python fine_tune.py --model "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"',
        styles,
    ))

    story.append(Paragraph(
        "Tip: Start with llama-3.2-3b for fast experimentation, then scale up to "
        "llama-3.1-8b or mistral-7b for production quality.",
        styles["Tip"],
    ))
    story.append(PageBreak())


def add_troubleshooting(story, styles):
    story.append(Paragraph("8.  Troubleshooting &amp; Tips", styles["SectionHead"]))

    story.append(Paragraph("Common Errors", styles["SubHead"]))

    story.append(Paragraph("CUDA Out of Memory (OOM)", styles["SubSubHead"]))
    story.append(bullet("Reduce batch_size to 1", styles))
    story.append(bullet("Reduce max_seq_length to 1024 or 512", styles))
    story.append(bullet("Use a smaller model (3B instead of 8B)", styles))
    story.append(bullet("Ensure gradient_checkpointing is 'unsloth'", styles))
    story.append(code(
        "python fine_tune.py --batch-size 1 --max-seq-length 1024 --model-alias llama-3.2-3b",
        styles,
    ))

    story.append(Paragraph("Model outputs gibberish after fine-tuning", styles["SubSubHead"]))
    story.append(bullet("Check training data quality - garbage in, garbage out", styles))
    story.append(bullet("Reduce epochs (you may be overfitting)", styles))
    story.append(bullet("Increase dataset size (100+ examples minimum)", styles))
    story.append(bullet("Lower learning rate to 1e-4", styles))

    story.append(Paragraph("'ollama create' fails", styles["SubSubHead"]))
    story.append(bullet("Make sure Ollama is running: <b>ollama serve</b>", styles))
    story.append(bullet("Check the GGUF file path in the Modelfile is absolute", styles))
    story.append(bullet("Try: <b>ollama create model-name -f ./output/Modelfile</b>", styles))

    story.append(Paragraph("Best Practices", styles["SubHead"]))
    story.append(Spacer(1, 4))

    practices = [
        "<b>Data quality over quantity</b> - 200 high-quality examples often beat 2000 mediocre ones",
        "<b>Match the chat format</b> - Use the exact system/user/assistant structure",
        "<b>Be consistent</b> - Same style, tone, and format across all examples",
        "<b>Include edge cases</b> - Train on the hard cases, not just easy ones",
        "<b>Validate first</b> - Run prepare_data.py with --validate-only before training",
        "<b>Start small</b> - Test with 3B model and 50 examples before scaling up",
        "<b>Monitor loss</b> - Training loss should decrease smoothly; spikes = bad data",
        "<b>Use q4_k_m</b> - Best quality/size tradeoff for most deployments",
    ]
    for p in practices:
        story.append(bullet(p, styles))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("End-to-End Example (Copy-Paste Ready)", styles["SubHead"]))
    story.append(code(
        "# 1. Prepare data\n"
        "python prepare_data.py \\\n"
        "    --input my_training_data.csv \\\n"
        "    --output data/train.jsonl \\\n"
        '    --system-prompt "You are an expert Python developer."\n'
        "\n"
        "# 2. Fine-tune (uses ~10 GB VRAM)\n"
        "python fine_tune.py \\\n"
        "    --model-alias llama-3.1-8b \\\n"
        "    --dataset data/train.jsonl \\\n"
        "    --epochs 3 \\\n"
        "    --lr 2e-4 \\\n"
        "    --output ./output\n"
        "\n"
        "# 3. Export and create Ollama model\n"
        "python export_to_ollama.py \\\n"
        "    --model-dir ./output \\\n"
        "    --model-name my-python-expert \\\n"
        "    --quantization q4_k_m \\\n"
        '    --system-prompt "You are an expert Python developer."\n'
        "\n"
        "# 4. Run it!\n"
        "ollama run my-python-expert",
        styles,
    ))

    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", color=BLUE, thickness=1))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "All code is available in the <b>ollama_fine_tune/</b> directory of this repository.",
        styles["Body"],
    ))


def add_page_number(canvas_obj, doc):
    page_num = canvas_obj.getPageNumber()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(GRAY)
    canvas_obj.drawRightString(
        letter[0] - 0.75 * inch,
        0.5 * inch,
        f"Page {page_num}",
    )
    canvas_obj.drawString(
        0.75 * inch,
        0.5 * inch,
        "Complete Guide: Fine-Tuning LLMs for Ollama",
    )


def main():
    output_path = "/home/user/python-projects/ollama_fine_tune/Fine_Tuning_LLMs_for_Ollama_Guide.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = build_styles()
    story = []

    add_cover(story, styles)
    add_toc(story, styles)
    add_overview(story, styles)
    add_prerequisites(story, styles)
    add_step1_data(story, styles)
    add_step2_finetune(story, styles)
    add_step3_export(story, styles)
    add_config_reference(story, styles)
    add_supported_models(story, styles)
    add_troubleshooting(story, styles)

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    main()
