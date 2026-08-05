"""Complete sklearn training pipeline.

Supports classification, regression, and text/NLP tasks.
Trains multiple models, compares them, and saves the best one.

Usage:
    # Classification
    python -m sklearn_pipeline.train --task classification --input data.csv --target label

    # Regression
    python -m sklearn_pipeline.train --task regression --input data.csv --target price

    # Text classification (NLP)
    python -m sklearn_pipeline.train --task text --input data.csv --text-col review --target sentiment

    # With custom test split
    python -m sklearn_pipeline.train --task classification --input data.csv --target label --test-size 0.3
"""

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, SGDClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

CLASSIFICATION_MODELS = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
    "SVM": SVC(kernel="rbf", random_state=42),
    "KNN": KNeighborsClassifier(n_neighbors=5),
    "Decision Tree": DecisionTreeClassifier(random_state=42),
}
if HAS_XGBOOST:
    CLASSIFICATION_MODELS["XGBoost"] = XGBClassifier(
        n_estimators=100, random_state=42, eval_metric="logloss",
    )

REGRESSION_MODELS = {
    "Linear Regression": LinearRegression(),
    "Ridge": Ridge(alpha=1.0),
    "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
    "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
    "SVR": SVR(kernel="rbf"),
    "Decision Tree": DecisionTreeRegressor(random_state=42),
}
if HAS_XGBOOST:
    REGRESSION_MODELS["XGBoost"] = XGBRegressor(
        n_estimators=100, random_state=42,
    )

TEXT_MODELS = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Naive Bayes": MultinomialNB(),
    "SGD Classifier": SGDClassifier(random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
}


def load_data(path: str) -> pd.DataFrame:
    p = Path(path)
    loaders = {
        ".csv": pd.read_csv,
        ".json": pd.read_json,
        ".jsonl": lambda f: pd.read_json(f, lines=True),
        ".xlsx": pd.read_excel,
        ".parquet": pd.read_parquet,
    }
    loader = loaders.get(p.suffix.lower())
    if not loader:
        raise ValueError(f"Unsupported format: {p.suffix}. Use csv, json, jsonl, xlsx, or parquet")
    return loader(path)


def train_classification(df, target_col, test_size, output_dir):
    print(f"\n{'='*60}")
    print(f"CLASSIFICATION TASK: Predicting '{target_col}'")
    print(f"{'='*60}")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    label_encoder = None
    if not pd.api.types.is_numeric_dtype(y):
        label_encoder = LabelEncoder()
        y = pd.Series(label_encoder.fit_transform(y))
        print(f"Classes: {list(label_encoder.classes_)}")

    X = pd.get_dummies(X, drop_first=True)
    X = X.fillna(X.median(numeric_only=True))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y,
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)} | Features: {X.shape[1]}")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = {}
    for name, model in CLASSIFICATION_MODELS.items():
        start = time.time()
        model.fit(X_train_scaled, y_train)
        elapsed = time.time() - start
        y_pred = model.predict(X_test_scaled)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted")
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring="accuracy")

        results[name] = {
            "accuracy": round(acc, 4),
            "f1_score": round(f1, 4),
            "cv_mean": round(cv_scores.mean(), 4),
            "cv_std": round(cv_scores.std(), 4),
            "train_time_sec": round(elapsed, 3),
        }
        print(f"  {name:25s} | Acc: {acc:.4f} | F1: {f1:.4f} | CV: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

    best_name = max(results, key=lambda k: results[k]["f1_score"])
    best_model = CLASSIFICATION_MODELS[best_name]
    best_model.fit(X_train_scaled, y_train)

    print(f"\nBest model: {best_name} (F1={results[best_name]['f1_score']})")
    print(f"\nClassification Report ({best_name}):")
    y_pred = best_model.predict(X_test_scaled)

    target_names = list(label_encoder.classes_) if label_encoder else None
    print(classification_report(y_test, y_pred, target_names=target_names))

    save_model(best_model, scaler, label_encoder, best_name, results, X.columns.tolist(),
               output_dir, "classification")


def train_regression(df, target_col, test_size, output_dir):
    print(f"\n{'='*60}")
    print(f"REGRESSION TASK: Predicting '{target_col}'")
    print(f"{'='*60}")

    X = df.drop(columns=[target_col])
    y = df[target_col].astype(float)

    X = pd.get_dummies(X, drop_first=True)
    X = X.fillna(X.median(numeric_only=True))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42,
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)} | Features: {X.shape[1]}")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = {}
    for name, model in REGRESSION_MODELS.items():
        start = time.time()
        model.fit(X_train_scaled, y_train)
        elapsed = time.time() - start
        y_pred = model.predict(X_test_scaled)

        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        results[name] = {
            "r2": round(r2, 4),
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "train_time_sec": round(elapsed, 3),
        }
        print(f"  {name:25s} | R2: {r2:.4f} | MAE: {mae:.4f} | RMSE: {rmse:.4f}")

    best_name = max(results, key=lambda k: results[k]["r2"])
    best_model = REGRESSION_MODELS[best_name]
    best_model.fit(X_train_scaled, y_train)

    print(f"\nBest model: {best_name} (R2={results[best_name]['r2']})")

    save_model(best_model, scaler, None, best_name, results, X.columns.tolist(),
               output_dir, "regression")


def train_text(df, text_col, target_col, test_size, output_dir):
    print(f"\n{'='*60}")
    print(f"TEXT CLASSIFICATION: '{text_col}' -> '{target_col}'")
    print(f"{'='*60}")

    X = df[text_col].astype(str)
    y = df[target_col]

    label_encoder = None
    if not pd.api.types.is_numeric_dtype(y):
        label_encoder = LabelEncoder()
        y = pd.Series(label_encoder.fit_transform(y))
        print(f"Classes: {list(label_encoder.classes_)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y,
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    tfidf = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)
    print(f"Vocabulary size: {len(tfidf.vocabulary_)}")

    results = {}
    for name, model in TEXT_MODELS.items():
        start = time.time()
        model.fit(X_train_tfidf, y_train)
        elapsed = time.time() - start
        y_pred = model.predict(X_test_tfidf)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted")

        results[name] = {
            "accuracy": round(acc, 4),
            "f1_score": round(f1, 4),
            "train_time_sec": round(elapsed, 3),
        }
        print(f"  {name:25s} | Acc: {acc:.4f} | F1: {f1:.4f}")

    best_name = max(results, key=lambda k: results[k]["f1_score"])
    best_model = TEXT_MODELS[best_name]
    best_model.fit(X_train_tfidf, y_train)

    print(f"\nBest model: {best_name} (F1={results[best_name]['f1_score']})")
    print(f"\nClassification Report ({best_name}):")
    y_pred = best_model.predict(X_test_tfidf)
    target_names = list(label_encoder.classes_) if label_encoder else None
    print(classification_report(y_test, y_pred, target_names=target_names))

    pipeline = Pipeline([
        ("tfidf", tfidf),
        ("model", best_model),
    ])

    save_model(pipeline, None, label_encoder, best_name, results, [text_col],
               output_dir, "text_classification")


def save_model(model, scaler, label_encoder, model_name, results, feature_names,
               output_dir, task_type):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, out / "model.joblib")
    if scaler:
        joblib.dump(scaler, out / "scaler.joblib")
    if label_encoder:
        joblib.dump(label_encoder, out / "label_encoder.joblib")

    metadata = {
        "task_type": task_type,
        "best_model": model_name,
        "feature_names": feature_names,
        "has_scaler": scaler is not None,
        "has_label_encoder": label_encoder is not None,
        "results": results,
    }
    with open(out / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved to {out}/:")
    print(f"  model.joblib        - trained {model_name}")
    if scaler:
        print(f"  scaler.joblib       - StandardScaler")
    if label_encoder:
        print(f"  label_encoder.joblib - LabelEncoder")
    print(f"  metadata.json       - results & config")


def main():
    parser = argparse.ArgumentParser(description="Train sklearn models")
    parser.add_argument("--task", required=True, choices=["classification", "regression", "text"],
                        help="Task type")
    parser.add_argument("--input", required=True, help="Path to dataset")
    parser.add_argument("--target", required=True, help="Target column name")
    parser.add_argument("--text-col", help="Text column (required for task=text)")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio (default 0.2)")
    parser.add_argument("--output", default="./sklearn_output", help="Output directory")
    args = parser.parse_args()

    if args.task == "text" and not args.text_col:
        parser.error("--text-col is required for task=text")

    df = load_data(args.input)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns from {args.input}")
    print(f"Columns: {list(df.columns)}")

    if args.target not in df.columns:
        raise ValueError(f"Target '{args.target}' not found. Available: {list(df.columns)}")

    if args.task == "classification":
        train_classification(df, args.target, args.test_size, args.output)
    elif args.task == "regression":
        train_regression(df, args.target, args.test_size, args.output)
    elif args.task == "text":
        train_text(df, args.text_col, args.target, args.test_size, args.output)


if __name__ == "__main__":
    main()
