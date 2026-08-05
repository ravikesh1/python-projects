"""Run all 3 task types with built-in sample datasets to demo the pipeline."""

import pandas as pd
from sklearn.datasets import (
    fetch_20newsgroups,
    load_iris,
    make_regression,
)

from sklearn_pipeline.train import train_classification, train_regression, train_text


def demo_classification():
    print("\n" + "#" * 70)
    print("# DEMO 1: Classification (Iris Dataset)")
    print("#" * 70)

    iris = load_iris()
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    df["species"] = [iris.target_names[t] for t in iris.target]
    df.to_csv("data/demo_iris.csv", index=False)
    print(f"Dataset: {len(df)} samples, {len(iris.feature_names)} features, 3 classes")

    train_classification(df, "species", test_size=0.2, output_dir="./sklearn_output/iris")


def demo_regression():
    print("\n" + "#" * 70)
    print("# DEMO 2: Regression (Synthetic Housing Data)")
    print("#" * 70)

    X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)
    df = pd.DataFrame(X, columns=["size", "bedrooms", "age", "distance", "quality"])
    df["price"] = y
    df.to_csv("data/demo_housing.csv", index=False)
    print(f"Dataset: {len(df)} samples, 5 features")

    train_regression(df, "price", test_size=0.2, output_dir="./sklearn_output/housing")


def demo_text():
    print("\n" + "#" * 70)
    print("# DEMO 3: Text Classification (Sentiment)")
    print("#" * 70)

    reviews = [
        ("This product is absolutely amazing, love it!", "positive"),
        ("Terrible quality, broke after one day", "negative"),
        ("Great value for the price, highly recommend", "positive"),
        ("Worst purchase ever, complete waste of money", "negative"),
        ("Exceeded my expectations, will buy again", "positive"),
        ("Does not work as advertised, very disappointed", "negative"),
        ("Perfect gift, my friend loved it", "positive"),
        ("Cheap material, fell apart immediately", "negative"),
        ("Outstanding quality and fast shipping", "positive"),
        ("Returned it the same day, horrible product", "negative"),
        ("Best purchase I made this year", "positive"),
        ("Do not buy this, save your money", "negative"),
        ("Works perfectly, exactly what I needed", "positive"),
        ("Misleading description, nothing like the photos", "negative"),
        ("Five stars, absolutely brilliant product", "positive"),
        ("One star, arrived damaged and seller ignored me", "negative"),
        ("I've bought three already for my family", "positive"),
        ("Flimsy and poorly made, not worth it", "negative"),
        ("Solid build quality, very impressed", "positive"),
        ("Total scam, fake product", "negative"),
        ("Beautiful design and works great", "positive"),
        ("Stopped working after a week", "negative"),
        ("My kids love it, great toy", "positive"),
        ("Overpriced for what you get", "negative"),
        ("Amazing customer service and product", "positive"),
        ("Never buying from this brand again", "negative"),
        ("Top notch quality, premium feel", "positive"),
        ("Instructions were confusing and missing parts", "negative"),
        ("So happy with this purchase!", "positive"),
        ("Absolute junk, don't waste your time", "negative"),
    ]
    df = pd.DataFrame(reviews, columns=["review", "sentiment"])
    df.to_csv("data/demo_sentiment.csv", index=False)
    print(f"Dataset: {len(df)} reviews, 2 classes")

    train_text(df, "review", "sentiment", test_size=0.2, output_dir="./sklearn_output/sentiment")


if __name__ == "__main__":
    from pathlib import Path
    Path("data").mkdir(exist_ok=True)

    demo_classification()
    demo_regression()
    demo_text()

    print("\n" + "=" * 70)
    print("ALL DEMOS COMPLETE!")
    print("=" * 70)
    print("\nSaved models:")
    print("  ./sklearn_output/iris/       - classification")
    print("  ./sklearn_output/housing/    - regression")
    print("  ./sklearn_output/sentiment/  - text classification")
    print("\nTo make predictions:")
    print('  python -m sklearn_pipeline.predict --model-dir ./sklearn_output/iris --input \'{"sepal length (cm)": 5.1, "sepal width (cm)": 3.5, "petal length (cm)": 1.4, "petal width (cm)": 0.2}\'')
    print('  python -m sklearn_pipeline.predict --model-dir ./sklearn_output/sentiment --input "This product is great!"')
