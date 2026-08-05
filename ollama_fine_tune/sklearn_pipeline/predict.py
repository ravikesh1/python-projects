"""Load a saved sklearn model and make predictions.

Usage:
    # Single prediction (classification/regression)
    python -m sklearn_pipeline.predict --model-dir ./sklearn_output --input '{"age": 30, "salary": 50000}'

    # Text prediction
    python -m sklearn_pipeline.predict --model-dir ./sklearn_output --input "This product is amazing!"

    # Batch prediction from file
    python -m sklearn_pipeline.predict --model-dir ./sklearn_output --input new_data.csv --output predictions.csv
"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def load_model(model_dir: str):
    d = Path(model_dir)
    model = joblib.load(d / "model.joblib")

    with open(d / "metadata.json") as f:
        metadata = json.load(f)

    scaler = None
    if metadata["has_scaler"]:
        scaler = joblib.load(d / "scaler.joblib")

    label_encoder = None
    if metadata["has_label_encoder"]:
        label_encoder = joblib.load(d / "label_encoder.joblib")

    return model, scaler, label_encoder, metadata


def predict_single(model, scaler, label_encoder, metadata, input_data):
    task = metadata["task_type"]

    if task == "text_classification":
        if isinstance(input_data, str):
            pred = model.predict([input_data])
            proba = model.predict_proba([input_data]) if hasattr(model, "predict_proba") else None
        else:
            raise ValueError("Text task expects a string input")
    else:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)
        df = pd.DataFrame([input_data])
        df = pd.get_dummies(df, drop_first=True)

        for col in metadata["feature_names"]:
            if col not in df.columns:
                df[col] = 0
        df = df[metadata["feature_names"]]
        df = df.fillna(0)

        if scaler:
            df = scaler.transform(df)
        pred = model.predict(df)
        proba = model.predict_proba(df) if hasattr(model, "predict_proba") else None

    result = {"prediction": pred[0]}
    if label_encoder:
        result["prediction"] = label_encoder.inverse_transform(pred)[0]
    if proba is not None and label_encoder:
        result["probabilities"] = {
            label_encoder.classes_[i]: round(float(p), 4)
            for i, p in enumerate(proba[0])
        }

    if isinstance(result["prediction"], np.integer):
        result["prediction"] = int(result["prediction"])
    elif isinstance(result["prediction"], np.floating):
        result["prediction"] = float(result["prediction"])

    return result


def predict_batch(model, scaler, label_encoder, metadata, input_path, output_path):
    task = metadata["task_type"]

    p = Path(input_path)
    if p.suffix == ".csv":
        df = pd.read_csv(input_path)
    elif p.suffix == ".json":
        df = pd.read_json(input_path)
    else:
        raise ValueError(f"Unsupported: {p.suffix}")

    if task == "text_classification":
        text_col = metadata["feature_names"][0]
        preds = model.predict(df[text_col])
    else:
        X = pd.get_dummies(df, drop_first=True)
        for col in metadata["feature_names"]:
            if col not in X.columns:
                X[col] = 0
        X = X[metadata["feature_names"]].fillna(0)
        if scaler:
            X = scaler.transform(X)
        preds = model.predict(X)

    if label_encoder:
        preds = label_encoder.inverse_transform(preds)

    df["prediction"] = preds
    df.to_csv(output_path, index=False)
    print(f"Predictions saved to {output_path} ({len(df)} rows)")


def main():
    parser = argparse.ArgumentParser(description="Make predictions with saved model")
    parser.add_argument("--model-dir", required=True, help="Directory with saved model")
    parser.add_argument("--input", required=True, help="Input data (JSON string, text, or file path)")
    parser.add_argument("--output", help="Output file for batch predictions")
    args = parser.parse_args()

    model, scaler, label_encoder, metadata = load_model(args.model_dir)
    print(f"Loaded {metadata['best_model']} ({metadata['task_type']})")

    input_path = Path(args.input)
    if input_path.exists():
        output = args.output or "predictions.csv"
        predict_batch(model, scaler, label_encoder, metadata, args.input, output)
    else:
        result = predict_single(model, scaler, label_encoder, metadata, args.input)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
