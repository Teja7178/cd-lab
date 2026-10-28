"""Train and evaluate the demo ML classifier."""
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from feature_extractor import FEATURE_NAMES, extract_features

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "code_samples.csv"
MODEL_DIR = ROOT / "models"
MODEL_PATH = MODEL_DIR / "inefficient_code_model.joblib"
METRICS_PATH = MODEL_DIR / "evaluation_metrics.json"

def main():
    df = pd.read_csv(DATA_PATH)
    required = {"source", "label"}
    if not required.issubset(df.columns):
        raise ValueError(f"Dataset must contain columns: {sorted(required)}")
    X = pd.DataFrame([extract_features(s) for s in df["source"].fillna("")])
    y = df["label"].astype(int)
    if y.nunique() < 2:
        raise ValueError("Dataset must include both labels 0 and 1.")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=200, random_state=42, class_weight="balanced",
        max_depth=8
    )
    model.fit(X_train[FEATURE_NAMES], y_train)
    pred = model.predict(X_test[FEATURE_NAMES])
    metrics = {
        "dataset_rows": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, pred, zero_division=0)),
        "confusion_matrix_labels_0_1": confusion_matrix(y_test, pred, labels=[0, 1]).tolist(),
        "classification_report": classification_report(y_test, pred, zero_division=0, output_dict=True),
        "warning": "Demo-only synthetic dataset; these metrics are not real-world performance evidence."
    }
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump({"model": model, "feature_names": FEATURE_NAMES}, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("Training complete.")
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved metrics: {METRICS_PATH}")
    print("\nDEMO DATA WARNING: included dataset is synthetic. Do not present these scores as validated research results.")
    print(f"Accuracy : {metrics['accuracy']:.3f}")
    print(f"Precision: {metrics['precision']:.3f}")
    print(f"Recall   : {metrics['recall']:.3f}")
    print(f"F1-score : {metrics['f1_score']:.3f}")
    print("Confusion matrix (rows=true labels 0,1; columns=predicted 0,1):")
    print(metrics["confusion_matrix_labels_0_1"])

if __name__ == "__main__":
    main()
