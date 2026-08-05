"""Generate 'LoRA Study Notes: Complete Guide to Low-Rank Adaptation' PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Preformatted, HRFlowable,
)

BLUE = HexColor("#1a56db")
DARK = HexColor("#1e293b")
GRAY = HexColor("#475569")
LIGHT_BG = HexColor("#f1f5f9")
CODE_BG = HexColor("#f8fafc")
WHITE = HexColor("#ffffff")
GREEN = HexColor("#15803d")
ORANGE = HexColor("#c2410c")
PURPLE = HexColor("#7c3aed")


def build_styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("CoverTitle", parent=ss["Title"], fontSize=28, leading=34,
                          textColor=DARK, alignment=TA_CENTER, spaceAfter=12))
    ss.add(ParagraphStyle("CoverSub", parent=ss["Normal"], fontSize=14, leading=18,
                          textColor=GRAY, alignment=TA_CENTER, spaceAfter=6))
    ss.add(ParagraphStyle("Sec", parent=ss["Heading1"], fontSize=20, leading=26,
                          textColor=BLUE, spaceBefore=24, spaceAfter=10))
    ss.add(ParagraphStyle("Sub", parent=ss["Heading2"], fontSize=15, leading=20,
                          textColor=DARK, spaceBefore=16, spaceAfter=8))
    ss.add(ParagraphStyle("Sub3", parent=ss["Heading3"], fontSize=12, leading=16,
                          textColor=GRAY, spaceBefore=12, spaceAfter=6))
    ss.add(ParagraphStyle("Body", parent=ss["Normal"], fontSize=10, leading=14,
                          textColor=DARK, spaceAfter=8))
    ss.add(ParagraphStyle("Bul", parent=ss["Normal"], fontSize=10, leading=14,
                          textColor=DARK, leftIndent=20, bulletIndent=8, spaceAfter=4))
    ss.add(ParagraphStyle("CB", fontName="Courier", fontSize=8.5, leading=12,
                          textColor=DARK, backColor=CODE_BG, leftIndent=12, rightIndent=12,
                          spaceBefore=6, spaceAfter=10, borderColor=HexColor("#e2e8f0"),
                          borderWidth=0.5, borderPadding=8))
    ss.add(ParagraphStyle("Note", parent=ss["Normal"], fontSize=9.5, leading=13,
                          textColor=ORANGE, leftIndent=16, rightIndent=16,
                          spaceBefore=6, spaceAfter=10, backColor=HexColor("#fff7ed"),
                          borderColor=ORANGE, borderWidth=0.5, borderPadding=8))
    ss.add(ParagraphStyle("Tip", parent=ss["Normal"], fontSize=9.5, leading=13,
                          textColor=GREEN, leftIndent=16, rightIndent=16,
                          spaceBefore=6, spaceAfter=10, backColor=HexColor("#f0fdf4"),
                          borderColor=GREEN, borderWidth=0.5, borderPadding=8))
    ss.add(ParagraphStyle("Key", parent=ss["Normal"], fontSize=9.5, leading=13,
                          textColor=PURPLE, leftIndent=16, rightIndent=16,
                          spaceBefore=6, spaceAfter=10, backColor=HexColor("#f5f3ff"),
                          borderColor=PURPLE, borderWidth=0.5, borderPadding=8))
    return ss


def C(text, s):
    return Preformatted(text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), s["CB"])


def B(text, s):
    return Paragraph(f"&bull;  {text}", s["Bul"])


def T(data, widths, highlight_row=None):
    t = Table(data, colWidths=widths)
    style = [
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
    ]
    if highlight_row:
        style.append(("BACKGROUND", (0, highlight_row), (-1, highlight_row), HexColor("#e0f2fe")))
    t.setStyle(TableStyle(style))
    return t


def build(story, s):
    # ── Cover ──
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("LoRA Study Notes", s["CoverTitle"]))
    story.append(Paragraph("Low-Rank Adaptation of Large Language Models", s["CoverTitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("From Theory to Implementation", s["CoverSub"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Everything you need to understand, use, and tune LoRA", s["CoverSub"]))
    story.append(Spacer(1, 1.5 * inch))
    story.append(HRFlowable(width="60%", color=BLUE, thickness=2, spaceAfter=12))
    story.append(Paragraph("Based on the paper: LoRA: Low-Rank Adaptation of Large Language Models (Hu et al., 2021)", s["CoverSub"]))
    story.append(PageBreak())

    # ── TOC ──
    story.append(Paragraph("Table of Contents", s["Sec"]))
    for item in [
        "1.   What is LoRA? (The Big Picture)",
        "2.   The Math Behind LoRA (Simplified)",
        "3.   Why LoRA Works (Intuition)",
        "4.   LoRA vs Other Fine-Tuning Methods",
        "5.   Key Parameters Explained",
        "6.   Implementation with HuggingFace PEFT",
        "7.   Implementation with Unsloth (2x Faster)",
        "8.   QLoRA: LoRA + 4-bit Quantization",
        "9.   Which Layers to Target",
        "10.  Hyperparameter Tuning Guide",
        "11.  Common Mistakes &amp; Fixes",
        "12.  LoRA Variants &amp; Advanced Techniques",
        "13.  Quick Reference Cheat Sheet",
    ]:
        story.append(Paragraph(item, s["Body"]))
    story.append(PageBreak())

    # ── 1. What is LoRA ──
    story.append(Paragraph("1.  What is LoRA? (The Big Picture)", s["Sec"]))
    story.append(Paragraph(
        "LoRA (Low-Rank Adaptation) is a technique for fine-tuning large language models "
        "by training only a tiny fraction of the parameters. Instead of updating all the "
        "weights in a model (billions of parameters), LoRA freezes the original weights "
        "and injects small trainable matrices alongside them.",
        s["Body"]))
    story.append(Paragraph("The Core Idea in One Sentence", s["Sub"]))
    story.append(Paragraph(
        "<b>Instead of modifying a huge weight matrix W directly, LoRA adds a small "
        "low-rank update: W' = W + BA, where B and A are much smaller matrices.</b>",
        s["Key"]))
    story.append(Paragraph("Why This Matters", s["Sub"]))
    story.append(T([
        ["", "Full Fine-Tuning", "LoRA"],
        ["Parameters trained", "All (e.g., 7 billion)", "~0.1-2% (e.g., 4-80 million)"],
        ["GPU memory needed", "Very high (60+ GB for 7B)", "Much lower (8-16 GB for 7B)"],
        ["Training speed", "Slow", "2-10x faster"],
        ["Storage per model", "Full copy (~14 GB for 7B)", "Small adapter (~10-100 MB)"],
        ["Quality", "Best possible", "Near-identical for most tasks"],
        ["Multiple tasks", "One full model per task", "One base + tiny adapters"],
    ], [1.3 * inch, 2.3 * inch, 2.3 * inch]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "Key Insight: A 7B parameter model fine-tuned with LoRA might only train 4 million "
        "parameters (0.06%), yet achieve 95-100% of full fine-tuning quality.",
        s["Tip"]))
    story.append(PageBreak())

    # ── 2. The Math ──
    story.append(Paragraph("2.  The Math Behind LoRA (Simplified)", s["Sec"]))
    story.append(Paragraph("Standard Fine-Tuning", s["Sub"]))
    story.append(Paragraph(
        "In a neural network, each layer has a weight matrix <b>W</b> of size (d x d). "
        "During standard fine-tuning, we update W directly:",
        s["Body"]))
    story.append(C(
        "W_new = W_original + delta_W\n"
        "\n"
        "Where delta_W is the full-rank update matrix.\n"
        "Size of delta_W = d x d (same as W, millions of parameters)", s))

    story.append(Paragraph("LoRA's Trick: Low-Rank Decomposition", s["Sub"]))
    story.append(Paragraph(
        "LoRA replaces the large delta_W with two small matrices multiplied together:",
        s["Body"]))
    story.append(C(
        "Instead of:  delta_W          (d x d)     e.g., 4096 x 4096 = 16.7M params\n"
        "LoRA uses:   B x A             \n"
        "             B is (d x r)      e.g., 4096 x 16 = 65K params\n"
        "             A is (r x d)      e.g., 16 x 4096 = 65K params\n"
        "                                                  --------\n"
        "                               Total:              131K params (0.8% of original!)\n"
        "\n"
        "Where r = rank (typically 4, 8, 16, 32, or 64)\n"
        "\n"
        "The output of a LoRA layer:\n"
        "  h = W @ x + (B @ A) @ x * (alpha / r)\n"
        "      -----   ---------------\n"
        "      frozen   trainable (LoRA adapter)", s))

    story.append(Paragraph("Initialization", s["Sub"]))
    story.append(B("<b>Matrix A</b> is initialized with random Gaussian values", s))
    story.append(B("<b>Matrix B</b> is initialized to zeros", s))
    story.append(B("This means <b>BA = 0</b> at the start, so the model begins identical to the original", s))
    story.append(Paragraph(
        "Why zeros for B? At the start of training, the LoRA adapter has zero effect "
        "(BA = 0). The model starts from its pre-trained state and gradually learns "
        "the task-specific adaptation. This is much more stable than random initialization.",
        s["Key"]))
    story.append(PageBreak())

    # ── 3. Why it works ──
    story.append(Paragraph("3.  Why LoRA Works (Intuition)", s["Sec"]))
    story.append(Paragraph("The Low-Rank Hypothesis", s["Sub"]))
    story.append(Paragraph(
        "Research shows that the weight changes during fine-tuning live in a "
        "<b>low-dimensional subspace</b>. In other words, even though W is huge, the "
        "actual change needed (delta_W) has low rank - it can be represented by a much "
        "smaller matrix without losing important information.",
        s["Body"]))
    story.append(Paragraph("Analogy: The Adjustment Knobs", s["Sub"]))
    story.append(Paragraph(
        "Think of a pre-trained model as a complex machine with millions of knobs. "
        "Full fine-tuning adjusts ALL knobs. LoRA discovers that you only need to adjust "
        "a few key knobs (the low-rank subspace) to adapt the machine for a new task. "
        "The rest of the knobs are already set correctly from pre-training.",
        s["Body"]))
    story.append(Paragraph("Key Research Findings", s["Sub"]))
    story.append(B("The intrinsic dimensionality of fine-tuning is very low (Aghajanyan et al., 2020)", s))
    story.append(B("A rank of r=4 to r=16 captures most task-specific information", s))
    story.append(B("LoRA matches full fine-tuning on GLUE, GPT-2, GPT-3 benchmarks", s))
    story.append(B("Higher ranks show diminishing returns (r=64 is rarely better than r=16)", s))

    story.append(Paragraph("When LoRA Might Not Be Enough", s["Sub"]))
    story.append(B("Extreme domain shift (medical jargon from a general model)", s))
    story.append(B("Learning a completely new language the model has never seen", s))
    story.append(B("Tasks requiring fundamentally new capabilities (not just style/format)", s))
    story.append(Paragraph(
        "Note: Even in these cases, LoRA often gets 90%+ of full fine-tuning quality. "
        "The gap narrows further with higher rank and more training data.",
        s["Note"]))
    story.append(PageBreak())

    # ── 4. LoRA vs Others ──
    story.append(Paragraph("4.  LoRA vs Other Fine-Tuning Methods", s["Sec"]))
    story.append(T([
        ["Method", "What It Does", "Params\nTrained", "Memory", "Quality"],
        ["Full Fine-Tuning", "Updates all weights", "100%", "Very High", "Best"],
        ["LoRA", "Adds low-rank matrices\nto attention layers", "0.1-2%", "Low", "Near-best"],
        ["QLoRA", "LoRA + 4-bit\nquantization", "0.1-2%", "Very Low", "Near-best"],
        ["Prefix Tuning", "Prepends learned\nvirtual tokens", "0.1%", "Low", "Good"],
        ["Prompt Tuning", "Learns soft prompt\nembeddings", "0.01%", "Very Low", "Moderate"],
        ["Adapters", "Inserts small networks\nbetween layers", "1-5%", "Low", "Good"],
        ["BitFit", "Only trains bias\nterms", "0.05%", "Very Low", "Moderate"],
    ], [1.1 * inch, 1.5 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch], highlight_row=2))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "Tip: LoRA is the most popular PEFT method because it offers the best "
        "quality-to-efficiency ratio. QLoRA extends it further for even lower memory. "
        "Start with QLoRA unless you have abundant GPU memory.",
        s["Tip"]))

    story.append(Paragraph("LoRA Advantages Over Other Methods", s["Sub"]))
    story.append(B("<b>No inference latency</b> - adapters can be merged back into the base model", s))
    story.append(B("<b>Composable</b> - swap different LoRA adapters on the same base model", s))
    story.append(B("<b>Works on any linear layer</b> - attention, feedforward, embeddings", s))
    story.append(B("<b>Battle-tested</b> - used in production by major companies", s))
    story.append(PageBreak())

    # ── 5. Key Parameters ──
    story.append(Paragraph("5.  Key Parameters Explained", s["Sec"]))

    story.append(Paragraph("r (Rank) - The Most Important Parameter", s["Sub"]))
    story.append(Paragraph(
        "The rank <b>r</b> controls the size of the LoRA matrices and directly determines "
        "how much capacity the adapter has to learn new information.",
        s["Body"]))
    story.append(T([
        ["Rank (r)", "Params Added", "Use Case", "Quality"],
        ["4", "Very few (~33K)", "Simple style/format changes", "Good"],
        ["8", "Few (~65K)", "Single-task adaptation", "Good"],
        ["16", "Moderate (~131K)", "General fine-tuning (recommended)", "Very Good"],
        ["32", "More (~262K)", "Complex tasks, multiple skills", "Excellent"],
        ["64", "Many (~524K)", "Near full fine-tuning capacity", "Excellent"],
        ["128", "High (~1M)", "Rarely needed, diminishing returns", "Marginal gain"],
    ], [0.7 * inch, 1.2 * inch, 2.2 * inch, 1 * inch], highlight_row=3))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "Rule of Thumb: Start with r=16. Only increase if you see the model isn't "
        "learning enough (high training loss). Decrease to r=8 if you need to save memory.",
        s["Key"]))

    story.append(Paragraph("lora_alpha - Scaling Factor", s["Sub"]))
    story.append(Paragraph(
        "Controls how much the LoRA adapter's output is scaled before being added to "
        "the original layer output. The effective scaling is: <b>alpha / r</b>",
        s["Body"]))
    story.append(B("<b>alpha = r</b> (e.g., alpha=16, r=16): scaling = 1.0 (standard, recommended)", s))
    story.append(B("<b>alpha = 2*r</b> (e.g., alpha=32, r=16): scaling = 2.0 (stronger adaptation)", s))
    story.append(B("<b>alpha &lt; r</b> (e.g., alpha=8, r=16): scaling = 0.5 (gentler adaptation)", s))
    story.append(Paragraph(
        "Tip: Set alpha = r as your default. This gives a scaling factor of 1.0 and "
        "works well in most cases. Only change it if you're doing advanced tuning.",
        s["Tip"]))

    story.append(Paragraph("lora_dropout", s["Sub"]))
    story.append(B("<b>0.0</b> (recommended for Unsloth and most cases)", s))
    story.append(B("<b>0.05-0.1</b> for small datasets where overfitting is a risk", s))
    story.append(B("Standard dropout applied to the LoRA layers during training", s))
    story.append(PageBreak())

    # ── 6. HuggingFace PEFT ──
    story.append(Paragraph("6.  Implementation with HuggingFace PEFT", s["Sec"]))

    story.append(Paragraph("Installation", s["Sub"]))
    story.append(C("pip install peft transformers torch accelerate", s))

    story.append(Paragraph("Step 1: Load a Pre-trained Model", s["Sub"]))
    story.append(C(
        "from transformers import AutoModelForCausalLM, AutoTokenizer\n"
        "\n"
        "model_name = \"meta-llama/Llama-3.1-8B-Instruct\"\n"
        "\n"
        "tokenizer = AutoTokenizer.from_pretrained(model_name)\n"
        "model = AutoModelForCausalLM.from_pretrained(\n"
        "    model_name,\n"
        "    torch_dtype=\"auto\",\n"
        "    device_map=\"auto\",  # Automatically use available GPUs\n"
        ")", s))

    story.append(Paragraph("Step 2: Configure LoRA", s["Sub"]))
    story.append(C(
        "from peft import LoraConfig, get_peft_model, TaskType\n"
        "\n"
        "lora_config = LoraConfig(\n"
        "    r=16,                   # Rank\n"
        "    lora_alpha=16,          # Scaling (alpha/r = 1.0)\n"
        "    lora_dropout=0.0,       # No dropout\n"
        "    target_modules=[        # Which layers to adapt\n"
        "        \"q_proj\",            # Query projection\n"
        "        \"k_proj\",            # Key projection\n"
        "        \"v_proj\",            # Value projection\n"
        "        \"o_proj\",            # Output projection\n"
        "        \"gate_proj\",         # FFN gate\n"
        "        \"up_proj\",           # FFN up\n"
        "        \"down_proj\",         # FFN down\n"
        "    ],\n"
        "    task_type=TaskType.CAUSAL_LM,\n"
        "    bias=\"none\",\n"
        ")\n"
        "\n"
        "model = get_peft_model(model, lora_config)\n"
        "model.print_trainable_parameters()\n"
        "# Output: trainable params: 4,194,304 || all params: 8,030,261,248\n"
        "#         || trainable%: 0.0522", s))

    story.append(Paragraph("Step 3: Train", s["Sub"]))
    story.append(C(
        "from trl import SFTTrainer\n"
        "from transformers import TrainingArguments\n"
        "\n"
        "trainer = SFTTrainer(\n"
        "    model=model,\n"
        "    tokenizer=tokenizer,\n"
        "    train_dataset=dataset,\n"
        "    args=TrainingArguments(\n"
        "        output_dir=\"./lora_output\",\n"
        "        num_train_epochs=3,\n"
        "        per_device_train_batch_size=4,\n"
        "        gradient_accumulation_steps=4,\n"
        "        learning_rate=2e-4,\n"
        "        bf16=True,\n"
        "        logging_steps=10,\n"
        "    ),\n"
        "    max_seq_length=2048,\n"
        ")\n"
        "trainer.train()", s))

    story.append(Paragraph("Step 4: Save and Load the Adapter", s["Sub"]))
    story.append(C(
        "# Save only the LoRA adapter (small file, ~10-100 MB)\n"
        "model.save_pretrained(\"./lora_adapter\")\n"
        "\n"
        "# Later: load the adapter on top of the base model\n"
        "from peft import PeftModel\n"
        "\n"
        "base_model = AutoModelForCausalLM.from_pretrained(model_name)\n"
        "model = PeftModel.from_pretrained(base_model, \"./lora_adapter\")\n"
        "\n"
        "# Optional: merge adapter into base (no adapter overhead at inference)\n"
        "merged_model = model.merge_and_unload()\n"
        "merged_model.save_pretrained(\"./merged_model\")", s))
    story.append(PageBreak())

    # ── 7. Unsloth ──
    story.append(Paragraph("7.  Implementation with Unsloth (2x Faster)", s["Sec"]))
    story.append(Paragraph(
        "Unsloth patches the model for optimized training. Same LoRA, 2x faster, "
        "60% less memory. Recommended for most use cases.",
        s["Body"]))
    story.append(C(
        "from unsloth import FastLanguageModel\n"
        "\n"
        "# 1. Load (automatically downloads 4-bit quantized version)\n"
        "model, tokenizer = FastLanguageModel.from_pretrained(\n"
        "    model_name=\"unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit\",\n"
        "    max_seq_length=2048,\n"
        "    load_in_4bit=True,\n"
        ")\n"
        "\n"
        "# 2. Add LoRA adapters (Unsloth's optimized version)\n"
        "model = FastLanguageModel.get_peft_model(\n"
        "    model,\n"
        "    r=16,\n"
        "    lora_alpha=16,\n"
        "    lora_dropout=0.0,\n"
        "    target_modules=[\n"
        "        \"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\",\n"
        "        \"gate_proj\", \"up_proj\", \"down_proj\",\n"
        "    ],\n"
        "    use_gradient_checkpointing=\"unsloth\",  # 60% less VRAM\n"
        ")\n"
        "\n"
        "# 3. Train (same SFTTrainer as HuggingFace)\n"
        "from trl import SFTTrainer\n"
        "from transformers import TrainingArguments\n"
        "\n"
        "trainer = SFTTrainer(\n"
        "    model=model,\n"
        "    tokenizer=tokenizer,\n"
        "    train_dataset=dataset,\n"
        "    args=TrainingArguments(\n"
        "        output_dir=\"./output\",\n"
        "        num_train_epochs=3,\n"
        "        per_device_train_batch_size=2,\n"
        "        gradient_accumulation_steps=4,\n"
        "        learning_rate=2e-4,\n"
        "        bf16=True,\n"
        "    ),\n"
        "    max_seq_length=2048,\n"
        ")\n"
        "trainer.train()\n"
        "\n"
        "# 4. Save adapter\n"
        "model.save_pretrained(\"./output\")\n"
        "\n"
        "# 5. Export to GGUF for Ollama\n"
        "model.save_pretrained_gguf(\n"
        "    \"./output\", tokenizer,\n"
        "    quantization_method=\"q4_k_m\",\n"
        ")", s))
    story.append(Paragraph(
        "Tip: Unsloth is a drop-in replacement. Same PEFT/LoRA concepts, same "
        "SFTTrainer, just faster. Use it unless you have a specific reason not to.",
        s["Tip"]))
    story.append(PageBreak())

    # ── 8. QLoRA ──
    story.append(Paragraph("8.  QLoRA: LoRA + 4-bit Quantization", s["Sec"]))
    story.append(Paragraph(
        "QLoRA (Dettmers et al., 2023) combines LoRA with 4-bit quantization of the "
        "base model. The base weights are stored in 4-bit (NF4 format), while LoRA "
        "adapters remain in full precision (bf16/fp16).",
        s["Body"]))

    story.append(Paragraph("How QLoRA Reduces Memory", s["Sub"]))
    story.append(T([
        ["Component", "Full Fine-Tuning", "LoRA (fp16)", "QLoRA (4-bit)"],
        ["Base model weights", "~14 GB (fp16)", "~14 GB (fp16)", "~3.5 GB (4-bit)"],
        ["LoRA adapters", "N/A", "~100 MB", "~100 MB"],
        ["Optimizer states", "~28 GB", "~200 MB", "~200 MB"],
        ["Gradients", "~14 GB", "~100 MB", "~100 MB"],
        ["Total for 7B model", "~56 GB", "~15 GB", "~4 GB"],
    ], [1.3 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch], highlight_row=5))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("QLoRA Key Innovations", s["Sub"]))
    story.append(B("<b>NF4 (NormalFloat4)</b> - a 4-bit data type optimized for normally-distributed weights", s))
    story.append(B("<b>Double quantization</b> - quantizes the quantization constants to save more memory", s))
    story.append(B("<b>Paged optimizers</b> - uses CPU RAM for optimizer states when GPU runs out", s))

    story.append(Paragraph("QLoRA Implementation", s["Sub"]))
    story.append(C(
        "from transformers import BitsAndBytesConfig\n"
        "import torch\n"
        "\n"
        "# 4-bit quantization config\n"
        "bnb_config = BitsAndBytesConfig(\n"
        "    load_in_4bit=True,\n"
        "    bnb_4bit_quant_type=\"nf4\",        # NormalFloat4\n"
        "    bnb_4bit_compute_dtype=torch.bfloat16,\n"
        "    bnb_4bit_use_double_quant=True,    # Double quantization\n"
        ")\n"
        "\n"
        "model = AutoModelForCausalLM.from_pretrained(\n"
        "    model_name,\n"
        "    quantization_config=bnb_config,\n"
        "    device_map=\"auto\",\n"
        ")\n"
        "\n"
        "# Then apply LoRA as normal\n"
        "model = get_peft_model(model, lora_config)", s))
    story.append(Paragraph(
        "Note: When using Unsloth with load_in_4bit=True, QLoRA is applied "
        "automatically. No need for manual BitsAndBytes config.",
        s["Note"]))
    story.append(PageBreak())

    # ── 9. Target Modules ──
    story.append(Paragraph("9.  Which Layers to Target", s["Sec"]))
    story.append(Paragraph(
        "LoRA can be applied to any linear layer. The choice of which layers to target "
        "affects both quality and efficiency.",
        s["Body"]))

    story.append(Paragraph("Transformer Layer Architecture", s["Sub"]))
    story.append(C(
        "Transformer Block:\n"
        "|\n"
        "|-- Multi-Head Attention:\n"
        "|   |-- q_proj  (Query)     <-- LoRA target (always include)\n"
        "|   |-- k_proj  (Key)       <-- LoRA target (always include)\n"
        "|   |-- v_proj  (Value)     <-- LoRA target (always include)\n"
        "|   |-- o_proj  (Output)    <-- LoRA target (recommended)\n"
        "|\n"
        "|-- Feed-Forward Network (MLP):\n"
        "|   |-- gate_proj           <-- LoRA target (recommended)\n"
        "|   |-- up_proj             <-- LoRA target (recommended)\n"
        "|   |-- down_proj           <-- LoRA target (recommended)\n"
        "|\n"
        "|-- Layer Norm (not targeted by LoRA)", s))

    story.append(Paragraph("Targeting Strategies", s["Sub"]))
    story.append(T([
        ["Strategy", "Target Modules", "Params", "Quality", "When to Use"],
        ["Minimal", "q_proj, v_proj", "Fewest", "Good", "Quick experiments,\nvery low memory"],
        ["Attention Only", "q_proj, k_proj,\nv_proj, o_proj", "Low", "Very Good", "Standard tasks,\ngood default"],
        ["Full (Recommended)", "q,k,v,o_proj +\ngate,up,down_proj", "Moderate", "Best", "Production fine-tuning"],
        ["+ Embeddings", "All above +\nembed_tokens,\nlm_head", "Most", "Best+", "New vocabulary,\nnew languages"],
    ], [1 * inch, 1.3 * inch, 0.7 * inch, 0.7 * inch, 1.4 * inch], highlight_row=3))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Model-Specific Module Names", s["Sub"]))
    story.append(T([
        ["Model", "Attention", "FFN"],
        ["Llama 3 / 3.1 / 3.2", "q_proj, k_proj,\nv_proj, o_proj", "gate_proj, up_proj,\ndown_proj"],
        ["Mistral / Mixtral", "q_proj, k_proj,\nv_proj, o_proj", "gate_proj, up_proj,\ndown_proj"],
        ["Gemma 2", "q_proj, k_proj,\nv_proj, o_proj", "gate_proj, up_proj,\ndown_proj"],
        ["Phi-3", "qkv_proj, o_proj", "gate_up_proj,\ndown_proj"],
        ["Qwen 2.5", "q_proj, k_proj,\nv_proj, o_proj", "gate_proj, up_proj,\ndown_proj"],
        ["GPT-2 / GPT-NeoX", "q_proj, k_proj,\nv_proj, out_proj", "fc_in, fc_out"],
    ], [1.4 * inch, 1.8 * inch, 1.8 * inch]))
    story.append(PageBreak())

    # ── 10. Hyperparameter Tuning ──
    story.append(Paragraph("10.  Hyperparameter Tuning Guide", s["Sec"]))

    story.append(Paragraph("Recommended Starting Configuration", s["Sub"]))
    story.append(C(
        "# Start here for most tasks\n"
        "r = 16\n"
        "lora_alpha = 16          # alpha/r = 1.0\n"
        "lora_dropout = 0.0\n"
        "learning_rate = 2e-4\n"
        "num_epochs = 3\n"
        "batch_size = 2\n"
        "gradient_accumulation = 4  # Effective batch = 8\n"
        "max_seq_length = 2048\n"
        "warmup_steps = 5\n"
        "weight_decay = 0.01", s))

    story.append(Paragraph("Tuning Decision Tree", s["Sub"]))
    story.append(T([
        ["Symptom", "Diagnosis", "Fix"],
        ["Loss doesn't decrease", "Learning rate too low\nor rank too low", "Increase lr to 5e-4\nor increase r to 32"],
        ["Loss spikes/oscillates", "Learning rate too high", "Decrease lr to 1e-4\nor 5e-5"],
        ["Loss goes to ~0 quickly\nbut output is bad", "Overfitting", "Reduce epochs (1-2),\nadd more data,\nor add dropout 0.05"],
        ["Slow training", "Batch too small or\nsequence too long", "Increase batch size,\nreduce max_seq_length"],
        ["Out of memory (OOM)", "Model too large for\nyour GPU", "Reduce batch to 1,\nreduce seq_length,\nuse smaller model"],
        ["Output style is wrong\nbut content is OK", "Rank is fine,\nneed more data", "Add more examples\nthat show desired style"],
    ], [1.5 * inch, 1.5 * inch, 2 * inch]))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Dataset Size Guidelines", s["Sub"]))
    story.append(T([
        ["Dataset Size", "Epochs", "Learning Rate", "Expected Quality"],
        ["< 100 examples", "5-10", "1e-4", "Style transfer only"],
        ["100-500 examples", "3-5", "2e-4", "Good for specific tasks"],
        ["500-2000 examples", "2-3", "2e-4", "Very good quality"],
        ["2000-10000 examples", "1-2", "1e-4", "Excellent quality"],
        ["> 10000 examples", "1", "5e-5 to 1e-4", "Near full fine-tune"],
    ], [1.3 * inch, 0.8 * inch, 1.1 * inch, 1.6 * inch]))
    story.append(PageBreak())

    # ── 11. Common Mistakes ──
    story.append(Paragraph("11.  Common Mistakes &amp; Fixes", s["Sec"]))

    mistakes = [
        ("Setting rank too high (r=256)",
         "Wastes memory, doesn't improve quality, may overfit.",
         "Use r=16 as default. Only go to 32-64 if r=16 clearly underfits."),
        ("Mismatched alpha and r",
         "alpha=32 with r=4 means scaling=8, which causes unstable training.",
         "Set alpha = r for scaling of 1.0, or alpha = 2*r for slightly stronger."),
        ("Not using chat template",
         "Model learns wrong format, outputs garbled text.",
         "Always use tokenizer.apply_chat_template() to format training data."),
        ("Training on too-short sequences",
         "Model truncates long inputs at inference.",
         "Set max_seq_length to cover your longest expected input + output."),
        ("Forgetting to merge before export",
         "Deploying the adapter separately adds inference latency.",
         "Use model.merge_and_unload() before exporting to GGUF."),
        ("Using fp16 on non-Ampere GPUs",
         "Older GPUs (V100, T4) don't support bf16.",
         "Use fp16=True instead of bf16=True on pre-Ampere GPUs."),
        ("Not freezing the base model",
         "If using raw PEFT without Unsloth, base may still be trainable.",
         "LoRA automatically freezes base weights. Verify with print_trainable_parameters()."),
        ("Training too many epochs on small data",
         "Model memorizes training data, outputs exact copies.",
         "Use 1-3 epochs for small datasets. Watch for loss approaching 0."),
    ]
    for title, problem, fix in mistakes:
        story.append(Paragraph(f"<b>{title}</b>", s["Sub3"]))
        story.append(Paragraph(f"Problem: {problem}", s["Body"]))
        story.append(Paragraph(f"Fix: {fix}", s["Tip"]))
    story.append(PageBreak())

    # ── 12. Variants ──
    story.append(Paragraph("12.  LoRA Variants &amp; Advanced Techniques", s["Sec"]))

    story.append(T([
        ["Variant", "Key Idea", "When to Use"],
        ["LoRA (original)", "Low-rank decomposition\nof weight updates", "Default choice\nfor most tasks"],
        ["QLoRA", "LoRA + 4-bit\nquantized base model", "Limited GPU memory\n(most common)"],
        ["LoRA+", "Different learning rates\nfor A and B matrices", "Slightly better quality\nat same cost"],
        ["DoRA", "Decomposes into magnitude\n+ direction components", "Better quality on\nsome benchmarks"],
        ["rsLoRA", "Scales alpha by 1/sqrt(r)\ninstead of 1/r", "When using very\nhigh ranks (r>64)"],
        ["AdaLoRA", "Adaptively adjusts rank\nper layer during training", "When some layers need\nmore capacity"],
        ["LoRA-FA", "Freezes A after init,\nonly trains B", "Faster training,\nsimilar quality"],
    ], [1 * inch, 2 * inch, 1.5 * inch]))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Multi-Adapter / Adapter Composition", s["Sub"]))
    story.append(Paragraph(
        "One of LoRA's biggest advantages is that you can train multiple adapters for "
        "different tasks and swap/combine them at inference time:",
        s["Body"]))
    story.append(C(
        "from peft import PeftModel\n"
        "\n"
        "# Load base model once\n"
        "base = AutoModelForCausalLM.from_pretrained(\"meta-llama/...\")\n"
        "\n"
        "# Load different adapters for different tasks\n"
        "coding_model = PeftModel.from_pretrained(base, \"./coding_adapter\")\n"
        "medical_model = PeftModel.from_pretrained(base, \"./medical_adapter\")\n"
        "legal_model = PeftModel.from_pretrained(base, \"./legal_adapter\")\n"
        "\n"
        "# Each adapter is only 10-100 MB!\n"
        "# The base model (14 GB) is shared across all tasks", s))

    story.append(Paragraph(
        "Key Insight: This is LoRA's killer feature for production. One base model "
        "in GPU memory, with tiny adapters hot-swapped per request. This is how "
        "companies serve hundreds of custom models efficiently.",
        s["Key"]))
    story.append(PageBreak())

    # ── 13. Cheat Sheet ──
    story.append(Paragraph("13.  Quick Reference Cheat Sheet", s["Sec"]))

    story.append(Paragraph("Default Configuration (Copy-Paste Ready)", s["Sub"]))
    story.append(C(
        "# LoRA Config - works for 90% of use cases\n"
        "lora_config = LoraConfig(\n"
        "    r=16,\n"
        "    lora_alpha=16,\n"
        "    lora_dropout=0.0,\n"
        "    target_modules=[\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\",\n"
        "                    \"gate_proj\", \"up_proj\", \"down_proj\"],\n"
        "    task_type=TaskType.CAUSAL_LM,\n"
        "    bias=\"none\",\n"
        ")", s))

    story.append(Paragraph("Quick Decision Guide", s["Sub"]))
    story.append(T([
        ["Question", "Answer"],
        ["What rank should I use?", "Start with 16. Go to 32 if underfitting."],
        ["What alpha should I set?", "Same as r (e.g., r=16, alpha=16)."],
        ["Which modules to target?", "All 7: q,k,v,o_proj + gate,up,down_proj."],
        ["How many epochs?", "3 for 100-1000 examples. 1-2 for 1000+."],
        ["What learning rate?", "2e-4 as default. Lower for large datasets."],
        ["LoRA or QLoRA?", "QLoRA unless you have 40+ GB VRAM."],
        ["When to use full fine-tuning?", "Only if LoRA quality isn't enough AND\nyou have the GPU budget."],
    ], [2.2 * inch, 3.8 * inch]))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Memory Cheat Sheet (7B Model)", s["Sub"]))
    story.append(T([
        ["Method", "VRAM Needed", "Training Speed"],
        ["Full Fine-Tuning (fp16)", "~60 GB", "Baseline"],
        ["LoRA (fp16)", "~16 GB", "~1.5x faster"],
        ["QLoRA (4-bit)", "~6 GB", "~1.5x faster"],
        ["QLoRA + Unsloth", "~5 GB", "~3x faster"],
    ], [2 * inch, 1.5 * inch, 1.5 * inch], highlight_row=4))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Key Formulas", s["Sub"]))
    story.append(C(
        "Trainable params = 2 * r * d * num_target_modules * num_layers\n"
        "Scaling factor   = alpha / r\n"
        "Effective batch   = per_device_batch_size * gradient_accumulation_steps\n"
        "Adapter size     = trainable_params * 2 bytes (fp16)  # ~MB\n"
        "\n"
        "Example for Llama-3.1-8B (d=4096, 32 layers, 7 modules):\n"
        "  Trainable = 2 * 16 * 4096 * 7 * 32 = 29.4M params\n"
        "  Adapter size = 29.4M * 2 = ~59 MB", s))

    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="100%", color=BLUE, thickness=1))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "References: Hu et al. (2021) 'LoRA: Low-Rank Adaptation of Large Language Models'; "
        "Dettmers et al. (2023) 'QLoRA: Efficient Finetuning of Quantized Language Models'; "
        "Aghajanyan et al. (2020) 'Intrinsic Dimensionality Explains the Effectiveness of Language Model Fine-Tuning'",
        s["Body"]))


def page_footer(canvas_obj, doc):
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(GRAY)
    canvas_obj.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {canvas_obj.getPageNumber()}")
    canvas_obj.drawString(0.75 * inch, 0.5 * inch, "LoRA Study Notes")


def main():
    out = "/home/user/python-projects/ollama_fine_tune/LoRA_Study_Notes.pdf"
    doc = SimpleDocTemplate(out, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = build_styles()
    story = []
    build(story, styles)
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    print(f"PDF generated: {out}")


if __name__ == "__main__":
    main()
