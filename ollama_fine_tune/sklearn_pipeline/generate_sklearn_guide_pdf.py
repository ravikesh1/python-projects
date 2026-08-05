"""Generate 'Complete Guide: ML Training with Scikit-Learn' PDF."""

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
    ss.add(ParagraphStyle("CodeBlk", fontName="Courier", fontSize=8.5, leading=12,
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
    return ss


def C(text, s):
    return Preformatted(text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), s["CodeBlk"])


def B(text, s):
    return Paragraph(f"&bull;  {text}", s["Bul"])


def T(data, widths):
    t = Table(data, colWidths=widths)
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
    return t


def build(story, s):
    # ── Cover ──
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("Complete Guide", s["CoverTitle"]))
    story.append(Paragraph("ML Training with Scikit-Learn", s["CoverTitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Classification, Regression &amp; Text/NLP Pipelines", s["CoverSub"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Train, compare, and deploy sklearn models step by step", s["CoverSub"]))
    story.append(Spacer(1, 1.5 * inch))
    story.append(HRFlowable(width="60%", color=BLUE, thickness=2, spaceAfter=12))
    story.append(Paragraph("With complete code and working examples", s["CoverSub"]))
    story.append(PageBreak())

    # ── TOC ──
    story.append(Paragraph("Table of Contents", s["Sec"]))
    for item in [
        "1.  When to Use sklearn vs LLM Fine-Tuning",
        "2.  Installation &amp; Setup",
        "3.  Step 1: Prepare Your Data",
        "4.  Step 2: Train Classification Models",
        "5.  Step 3: Train Regression Models",
        "6.  Step 4: Train Text/NLP Models",
        "7.  Step 5: Make Predictions",
        "8.  Complete Training Script Reference",
        "9.  Model Comparison &amp; Selection Guide",
        "10. Tips &amp; Best Practices",
    ]:
        story.append(Paragraph(item, s["Body"]))
    story.append(PageBreak())

    # ── 1. When to Use ──
    story.append(Paragraph("1.  When to Use sklearn vs LLM Fine-Tuning", s["Sec"]))
    story.append(T([
        ["", "sklearn", "LLM Fine-Tuning (Ollama)"],
        ["Task", "Classification, regression,\nclustering, tabular data", "Text generation, chat,\nsummarization, reasoning"],
        ["Data", "Structured (CSV, tables)\n100-100K rows", "Unstructured text\n100-10K conversations"],
        ["Hardware", "CPU is fine\nNo GPU needed", "GPU required\n8-80 GB VRAM"],
        ["Training", "Seconds to minutes", "Minutes to hours"],
        ["Output", "Predictions (labels, numbers)", "Generated text"],
        ["Best For", "Business analytics, fraud,\nspam detection, pricing", "Chatbots, content gen,\ncode assistants"],
    ], [0.8 * inch, 2.5 * inch, 2.5 * inch]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "Tip: If your data fits in a spreadsheet and you need predictions (yes/no, "
        "price, category), use sklearn. If you need the model to generate text or hold "
        "conversations, use LLM fine-tuning.", s["Tip"]))
    story.append(PageBreak())

    # ── 2. Installation ──
    story.append(Paragraph("2.  Installation &amp; Setup", s["Sec"]))
    story.append(Paragraph("Install the required packages:", s["Body"]))
    story.append(C("pip install scikit-learn pandas numpy joblib xgboost", s))
    story.append(Paragraph("Verify installation:", s["Body"]))
    story.append(C(
        "import sklearn\n"
        "print(sklearn.__version__)  # Should be 1.3+", s))
    story.append(Paragraph(
        "Note: sklearn runs on CPU by default. No GPU or CUDA required. "
        "Works on any machine (laptop, server, cloud).", s["Note"]))
    story.append(PageBreak())

    # ── 3. Data Prep ──
    story.append(Paragraph("3.  Step 1: Prepare Your Data", s["Sec"]))
    story.append(Paragraph("For Classification / Regression (Tabular Data)", s["Sub"]))
    story.append(Paragraph("Create a CSV with feature columns and one target column:", s["Body"]))
    story.append(C(
        "age,salary,department,experience,promoted\n"
        "28,45000,engineering,3,yes\n"
        "35,72000,marketing,8,yes\n"
        "22,32000,sales,1,no\n"
        "45,95000,engineering,15,yes\n"
        "31,55000,marketing,5,no", s))
    story.append(Paragraph("For Text Classification (NLP)", s["Sub"]))
    story.append(C(
        "text,label\n"
        '"This product is amazing, love it!",positive\n'
        '"Terrible quality, would not buy again",negative\n'
        '"Great value for the price",positive\n'
        '"Worst purchase ever",negative', s))
    story.append(Paragraph("Loading Data in Code", s["Sub"]))
    story.append(C(
        "import pandas as pd\n\n"
        "# CSV\n"
        "df = pd.read_csv('data.csv')\n\n"
        "# JSON\n"
        "df = pd.read_json('data.json')\n\n"
        "# Excel\n"
        "df = pd.read_excel('data.xlsx')\n\n"
        "# Quick look at the data\n"
        "print(df.shape)        # (rows, columns)\n"
        "print(df.head())       # First 5 rows\n"
        "print(df.describe())   # Statistics\n"
        "print(df.isnull().sum())  # Missing values", s))
    story.append(PageBreak())

    # ── 4. Classification ──
    story.append(Paragraph("4.  Step 2: Train Classification Models", s["Sec"]))
    story.append(Paragraph("One-Command Training", s["Sub"]))
    story.append(C(
        "python -m sklearn_pipeline.train \\\n"
        "    --task classification \\\n"
        "    --input data.csv \\\n"
        "    --target label_column \\\n"
        "    --output ./sklearn_output/my_model", s))
    story.append(Paragraph(
        "This automatically trains 7 models, compares them, and saves the best one.", s["Body"]))
    story.append(Paragraph("Models Trained Automatically", s["Sub"]))
    story.append(T([
        ["Model", "Strengths", "Speed"],
        ["Logistic Regression", "Simple, interpretable, good baseline", "Very Fast"],
        ["Random Forest", "Handles non-linear data, robust", "Fast"],
        ["Gradient Boosting", "High accuracy, handles complex patterns", "Moderate"],
        ["XGBoost", "State-of-the-art for tabular data", "Moderate"],
        ["SVM", "Works well with high-dimensional data", "Slow on large data"],
        ["KNN", "Simple, no training phase", "Slow at prediction"],
        ["Decision Tree", "Most interpretable, visual", "Very Fast"],
    ], [1.5 * inch, 2.8 * inch, 1.3 * inch]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Complete Classification Code (Step by Step)", s["Sub"]))
    story.append(C(
        "import pandas as pd\n"
        "from sklearn.model_selection import train_test_split\n"
        "from sklearn.preprocessing import StandardScaler, LabelEncoder\n"
        "from sklearn.ensemble import RandomForestClassifier\n"
        "from sklearn.metrics import accuracy_score, classification_report\n"
        "\n"
        "# 1. Load data\n"
        "df = pd.read_csv('data.csv')\n"
        "\n"
        "# 2. Separate features and target\n"
        "X = df.drop(columns=['target_column'])\n"
        "y = df['target_column']\n"
        "\n"
        "# 3. Encode string labels to numbers\n"
        "le = LabelEncoder()\n"
        "y = le.fit_transform(y)\n"
        "\n"
        "# 4. Handle categorical columns\n"
        "X = pd.get_dummies(X, drop_first=True)\n"
        "\n"
        "# 5. Split into train/test\n"
        "X_train, X_test, y_train, y_test = train_test_split(\n"
        "    X, y, test_size=0.2, random_state=42, stratify=y\n"
        ")\n"
        "\n"
        "# 6. Scale features\n"
        "scaler = StandardScaler()\n"
        "X_train = scaler.fit_transform(X_train)\n"
        "X_test = scaler.transform(X_test)\n"
        "\n"
        "# 7. Train model\n"
        "model = RandomForestClassifier(n_estimators=100, random_state=42)\n"
        "model.fit(X_train, y_train)\n"
        "\n"
        "# 8. Evaluate\n"
        "y_pred = model.predict(X_test)\n"
        "print(f'Accuracy: {accuracy_score(y_test, y_pred):.4f}')\n"
        "print(classification_report(y_test, y_pred,\n"
        "      target_names=le.classes_))\n"
        "\n"
        "# 9. Save model\n"
        "import joblib\n"
        "joblib.dump(model, 'model.joblib')\n"
        "joblib.dump(scaler, 'scaler.joblib')\n"
        "joblib.dump(le, 'label_encoder.joblib')", s))
    story.append(PageBreak())

    # ── 5. Regression ──
    story.append(Paragraph("5.  Step 3: Train Regression Models", s["Sec"]))
    story.append(Paragraph("One-Command Training", s["Sub"]))
    story.append(C(
        "python -m sklearn_pipeline.train \\\n"
        "    --task regression \\\n"
        "    --input housing.csv \\\n"
        "    --target price", s))
    story.append(Paragraph("Models Trained Automatically", s["Sub"]))
    story.append(T([
        ["Model", "Best For", "Metric"],
        ["Linear Regression", "Linear relationships", "R2, RMSE"],
        ["Ridge", "Multicollinearity", "R2, RMSE"],
        ["Random Forest", "Non-linear patterns", "R2, RMSE"],
        ["Gradient Boosting", "Complex relationships", "R2, RMSE"],
        ["XGBoost", "Tabular data competitions", "R2, RMSE"],
        ["SVR", "Small datasets, non-linear", "R2, RMSE"],
        ["Decision Tree", "Interpretability needed", "R2, RMSE"],
    ], [1.5 * inch, 2.3 * inch, 1.2 * inch]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Complete Regression Code", s["Sub"]))
    story.append(C(
        "import pandas as pd\n"
        "from sklearn.model_selection import train_test_split\n"
        "from sklearn.preprocessing import StandardScaler\n"
        "from sklearn.ensemble import GradientBoostingRegressor\n"
        "from sklearn.metrics import r2_score, mean_absolute_error\n"
        "import numpy as np\n"
        "\n"
        "# 1. Load and split\n"
        "df = pd.read_csv('housing.csv')\n"
        "X = df.drop(columns=['price'])\n"
        "y = df['price']\n"
        "X = pd.get_dummies(X, drop_first=True)\n"
        "X_train, X_test, y_train, y_test = train_test_split(\n"
        "    X, y, test_size=0.2, random_state=42\n"
        ")\n"
        "\n"
        "# 2. Scale and train\n"
        "scaler = StandardScaler()\n"
        "X_train = scaler.fit_transform(X_train)\n"
        "X_test = scaler.transform(X_test)\n"
        "model = GradientBoostingRegressor(\n"
        "    n_estimators=100, random_state=42\n"
        ")\n"
        "model.fit(X_train, y_train)\n"
        "\n"
        "# 3. Evaluate\n"
        "y_pred = model.predict(X_test)\n"
        "print(f'R2:   {r2_score(y_test, y_pred):.4f}')\n"
        "print(f'MAE:  {mean_absolute_error(y_test, y_pred):.4f}')\n"
        "rmse = np.sqrt(np.mean((y_test - y_pred)**2))\n"
        "print(f'RMSE: {rmse:.4f}')", s))
    story.append(PageBreak())

    # ── 6. Text/NLP ──
    story.append(Paragraph("6.  Step 4: Train Text/NLP Models", s["Sec"]))
    story.append(Paragraph("One-Command Training", s["Sub"]))
    story.append(C(
        "python -m sklearn_pipeline.train \\\n"
        "    --task text \\\n"
        "    --input reviews.csv \\\n"
        "    --text-col review \\\n"
        "    --target sentiment", s))
    story.append(Paragraph("How It Works: TF-IDF + Classifier", s["Sub"]))
    story.append(Paragraph(
        "Text is converted to numbers using TF-IDF (Term Frequency-Inverse Document "
        "Frequency), which scores how important each word is to a document relative "
        "to the entire corpus. Then a classifier is trained on these features.", s["Body"]))
    story.append(Paragraph("Complete Text Classification Code", s["Sub"]))
    story.append(C(
        "import pandas as pd\n"
        "from sklearn.feature_extraction.text import TfidfVectorizer\n"
        "from sklearn.linear_model import LogisticRegression\n"
        "from sklearn.pipeline import Pipeline\n"
        "from sklearn.model_selection import train_test_split\n"
        "from sklearn.metrics import classification_report\n"
        "\n"
        "# 1. Load data\n"
        "df = pd.read_csv('reviews.csv')\n"
        "X_train, X_test, y_train, y_test = train_test_split(\n"
        "    df['review'], df['sentiment'],\n"
        "    test_size=0.2, random_state=42\n"
        ")\n"
        "\n"
        "# 2. Build pipeline (TF-IDF + model in one object)\n"
        "pipeline = Pipeline([\n"
        "    ('tfidf', TfidfVectorizer(\n"
        "        max_features=10000,\n"
        "        ngram_range=(1, 2),   # unigrams + bigrams\n"
        "        min_df=2,\n"
        "        max_df=0.95,\n"
        "        sublinear_tf=True,\n"
        "    )),\n"
        "    ('model', LogisticRegression(\n"
        "        max_iter=1000, random_state=42\n"
        "    )),\n"
        "])\n"
        "\n"
        "# 3. Train\n"
        "pipeline.fit(X_train, y_train)\n"
        "\n"
        "# 4. Evaluate\n"
        "y_pred = pipeline.predict(X_test)\n"
        "print(classification_report(y_test, y_pred))\n"
        "\n"
        "# 5. Predict new text\n"
        "print(pipeline.predict(['This product is amazing!']))\n"
        "# Output: ['positive']\n"
        "\n"
        "# 6. Save the entire pipeline\n"
        "import joblib\n"
        "joblib.dump(pipeline, 'text_model.joblib')", s))
    story.append(Paragraph(
        "Tip: The Pipeline object bundles TF-IDF + model together, so you only "
        "need to save/load one file. Pass raw text directly - no manual "
        "preprocessing needed.", s["Tip"]))
    story.append(PageBreak())

    # ── 7. Predictions ──
    story.append(Paragraph("7.  Step 5: Make Predictions", s["Sec"]))
    story.append(Paragraph("Single Prediction (Classification)", s["Sub"]))
    story.append(C(
        'python -m sklearn_pipeline.predict \\\n'
        '    --model-dir ./sklearn_output/iris \\\n'
        '    --input \'{"sepal length (cm)": 5.1, "sepal width (cm)": 3.5,\n'
        '              "petal length (cm)": 1.4, "petal width (cm)": 0.2}\'\n'
        '\n'
        '# Output:\n'
        '# {\n'
        '#   "prediction": "setosa",\n'
        '#   "probabilities": {"setosa": 1.0, "versicolor": 0.0, ...}\n'
        '# }', s))
    story.append(Paragraph("Single Prediction (Text)", s["Sub"]))
    story.append(C(
        'python -m sklearn_pipeline.predict \\\n'
        '    --model-dir ./sklearn_output/sentiment \\\n'
        '    --input "This product is great!"\n'
        '\n'
        '# Output:\n'
        '# {\n'
        '#   "prediction": "positive",\n'
        '#   "probabilities": {"negative": 0.42, "positive": 0.58}\n'
        '# }', s))
    story.append(Paragraph("Batch Prediction from File", s["Sub"]))
    story.append(C(
        "python -m sklearn_pipeline.predict \\\n"
        "    --model-dir ./sklearn_output/iris \\\n"
        "    --input new_data.csv \\\n"
        "    --output predictions.csv", s))
    story.append(Paragraph("Loading a Saved Model in Your Own Code", s["Sub"]))
    story.append(C(
        "import joblib\n"
        "\n"
        "# Load\n"
        "model = joblib.load('sklearn_output/iris/model.joblib')\n"
        "scaler = joblib.load('sklearn_output/iris/scaler.joblib')\n"
        "le = joblib.load('sklearn_output/iris/label_encoder.joblib')\n"
        "\n"
        "# Predict\n"
        "import numpy as np\n"
        "X_new = np.array([[5.1, 3.5, 1.4, 0.2]])\n"
        "X_scaled = scaler.transform(X_new)\n"
        "pred = model.predict(X_scaled)\n"
        "label = le.inverse_transform(pred)\n"
        "print(label)  # ['setosa']", s))
    story.append(PageBreak())

    # ── 8. Script Reference ──
    story.append(Paragraph("8.  Complete Training Script Reference", s["Sec"]))
    story.append(Paragraph("All CLI Options", s["Sub"]))
    story.append(T([
        ["Flag", "Required", "Default", "Description"],
        ["--task", "Yes", "-", "classification, regression,\nor text"],
        ["--input", "Yes", "-", "Path to CSV, JSON, JSONL,\nXLSX, or Parquet"],
        ["--target", "Yes", "-", "Target column name"],
        ["--text-col", "text only", "-", "Text column name\n(required for task=text)"],
        ["--test-size", "No", "0.2", "Fraction of data for testing\n(0.1 to 0.4)"],
        ["--output", "No", "./sklearn_output", "Where to save the\ntrained model"],
    ], [1 * inch, 0.8 * inch, 1.1 * inch, 2.6 * inch]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Output Files", s["Sub"]))
    story.append(T([
        ["File", "Description"],
        ["model.joblib", "Trained model (or Pipeline for text tasks)"],
        ["scaler.joblib", "StandardScaler (classification/regression only)"],
        ["label_encoder.joblib", "LabelEncoder (when target is categorical)"],
        ["metadata.json", "Model name, metrics, feature names, config"],
    ], [2 * inch, 4 * inch]))
    story.append(PageBreak())

    # ── 9. Model Selection ──
    story.append(Paragraph("9.  Model Comparison &amp; Selection Guide", s["Sec"]))
    story.append(Paragraph("Choosing the Right Model", s["Sub"]))
    story.append(T([
        ["Scenario", "Recommended Model", "Why"],
        ["< 1K rows", "Logistic Regression /\nLinear Regression", "Simple models generalize\nbetter on small data"],
        ["1K-100K rows", "Gradient Boosting /\nXGBoost", "Best accuracy on\nmedium datasets"],
        ["> 100K rows", "SGD / Random Forest", "Scales well to\nlarge datasets"],
        ["Need interpretability", "Decision Tree /\nLogistic Regression", "Easy to explain\nto stakeholders"],
        ["Text classification", "Logistic Regression +\nTF-IDF", "Fast and effective\nfor most NLP tasks"],
        ["Many features", "Random Forest /\nXGBoost", "Handles high-dimensional\ndata well"],
    ], [1.4 * inch, 1.7 * inch, 2 * inch]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Evaluation Metrics Explained", s["Sub"]))
    story.append(T([
        ["Metric", "Task", "Meaning", "Good Value"],
        ["Accuracy", "Classification", "% of correct predictions", "> 0.85"],
        ["F1 Score", "Classification", "Balance of precision & recall", "> 0.80"],
        ["R2", "Regression", "% of variance explained", "> 0.70"],
        ["MAE", "Regression", "Average absolute error", "As low as possible"],
        ["RMSE", "Regression", "Root mean squared error", "As low as possible"],
    ], [0.9 * inch, 1.1 * inch, 2.2 * inch, 1.2 * inch]))
    story.append(PageBreak())

    # ── 10. Tips ──
    story.append(Paragraph("10.  Tips &amp; Best Practices", s["Sec"]))
    story.append(Paragraph("Data Preparation", s["Sub"]))
    story.append(B("<b>Handle missing values</b> - fill with median (numbers) or mode (categories)", s))
    story.append(B("<b>Remove duplicates</b> - df.drop_duplicates()", s))
    story.append(B("<b>Check class balance</b> - imbalanced classes hurt accuracy", s))
    story.append(B("<b>Feature engineering</b> - create new features from existing ones", s))
    story.append(C(
        "# Handle imbalanced classes\n"
        "from sklearn.utils import class_weight\n"
        "weights = class_weight.compute_class_weight(\n"
        "    'balanced', classes=np.unique(y_train), y=y_train\n"
        ")\n"
        "model = RandomForestClassifier(\n"
        "    class_weight='balanced', random_state=42\n"
        ")", s))

    story.append(Paragraph("Improve Model Performance", s["Sub"]))
    story.append(B("<b>Cross-validation</b> - use 5-fold CV instead of single train/test", s))
    story.append(B("<b>Hyperparameter tuning</b> - use GridSearchCV or RandomizedSearchCV", s))
    story.append(B("<b>Feature selection</b> - remove irrelevant features", s))
    story.append(C(
        "# Hyperparameter tuning example\n"
        "from sklearn.model_selection import GridSearchCV\n"
        "\n"
        "param_grid = {\n"
        "    'n_estimators': [100, 200, 500],\n"
        "    'max_depth': [3, 5, 10, None],\n"
        "    'min_samples_split': [2, 5, 10],\n"
        "}\n"
        "\n"
        "grid = GridSearchCV(\n"
        "    RandomForestClassifier(random_state=42),\n"
        "    param_grid, cv=5, scoring='f1_weighted', n_jobs=-1\n"
        ")\n"
        "grid.fit(X_train, y_train)\n"
        "print(f'Best params: {grid.best_params_}')\n"
        "print(f'Best score:  {grid.best_score_:.4f}')\n"
        "best_model = grid.best_estimator_", s))

    story.append(Paragraph("sklearn vs LLM: Decision Flowchart", s["Sub"]))
    story.append(B("Is your data in a table/spreadsheet? -> <b>sklearn</b>", s))
    story.append(B("Do you need to generate text? -> <b>LLM fine-tuning</b>", s))
    story.append(B("Is your task classification/regression? -> <b>sklearn</b>", s))
    story.append(B("Do you need conversational AI? -> <b>LLM fine-tuning</b>", s))
    story.append(B("Budget under $0 for compute? -> <b>sklearn</b> (runs on CPU)", s))

    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", color=BLUE, thickness=1))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "All code is available in <b>ollama_fine_tune/sklearn_pipeline/</b>. "
        "Run the demo with: <b>python -m sklearn_pipeline.demo</b>", s["Body"]))


def page_footer(canvas_obj, doc):
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(GRAY)
    canvas_obj.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {canvas_obj.getPageNumber()}")
    canvas_obj.drawString(0.75 * inch, 0.5 * inch, "ML Training with Scikit-Learn")


def main():
    out = "/home/user/python-projects/ollama_fine_tune/sklearn_pipeline/Sklearn_Training_Guide.pdf"
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
