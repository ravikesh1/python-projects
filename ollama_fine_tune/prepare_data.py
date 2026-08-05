"""Convert raw data into the chat format required for fine-tuning.

Supported input formats:
  - CSV  with columns: instruction, input (optional), output
  - JSON with the same fields
  - JSONL already in chat format (passed through)

Output: JSONL where each line is a list of chat messages:
  [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
"""

import argparse
import csv
import json
from pathlib import Path


def convert_row_to_chat(row: dict, system_prompt: str) -> list[dict]:
    user_content = row["instruction"]
    if row.get("input"):
        user_content += f"\n\n{row['input']}"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_content})
    messages.append({"role": "assistant", "content": row["output"]})
    return messages


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Prepare training data for fine-tuning")
    parser.add_argument("--input", required=True, help="Path to input file (CSV, JSON, or JSONL)")
    parser.add_argument("--output", default="data/train.jsonl", help="Output JSONL path")
    parser.add_argument(
        "--system-prompt",
        default="You are a helpful assistant.",
        help="System prompt to prepend to each conversation",
    )
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't write")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        rows = load_csv(input_path)
    elif suffix == ".json":
        rows = load_json(input_path)
    elif suffix == ".jsonl":
        rows = load_jsonl(input_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv, .json, or .jsonl")

    conversations = []
    already_chat_format = False

    for i, row in enumerate(rows):
        if isinstance(row, list) and all(isinstance(m, dict) and "role" in m for m in row):
            already_chat_format = True
            conversations.append(row)
            continue

        if isinstance(row, dict) and "messages" in row:
            already_chat_format = True
            conversations.append(row["messages"])
            continue

        required = {"instruction", "output"}
        missing = required - set(row.keys())
        if missing:
            raise ValueError(f"Row {i} missing required fields: {missing}")
        conversations.append(convert_row_to_chat(row, args.system_prompt))

    print(f"Processed {len(conversations)} training examples")
    if conversations:
        print(f"Sample conversation:\n{json.dumps(conversations[0], indent=2)}")

    if args.validate_only:
        print("Validation passed.")
        return

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for conv in conversations:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")

    format_note = "already in chat format" if already_chat_format else "converted to chat format"
    print(f"Wrote {len(conversations)} examples ({format_note}) to {output_path}")


if __name__ == "__main__":
    main()
