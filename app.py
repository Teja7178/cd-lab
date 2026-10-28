"""Flask Web Application for ML-Based Inefficient Code Pattern Detector."""
from pathlib import Path
import json
import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify
from feature_extractor import FEATURE_NAMES, extract_features, heuristic_evidence

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "inefficient_code_model.joblib"
METRICS_PATH = ROOT / "models" / "evaluation_metrics.json"

app = Flask(__name__)

# Sample code snippets for instant testing
PRESETS = {
    "inefficient_strlen": {
        "title": "sample_inefficient.c (Loop-Invariant strlen)",
        "code": """#include <stdio.h>
#include <string.h>

int main(void) {
    char name[] = "compiler";
    int total = 0;
    for (int i = 0; i < 100; i++) {
        int length = (int)strlen(name); /* Invariant calculation recalculated 100x */
        if (i < length) {
            total += i;
        }
    }
    printf("%d\\n", total);
    return 0;
}"""
    },
    "clean_sum": {
        "title": "sample_clean.c (Optimized Array Sum)",
        "code": """#include <stdio.h>

int main(void) {
    int values[] = {1, 2, 3, 4, 5};
    int total = 0;
    int count = 5;
    for (int i = 0; i < count; i++) {
        total += values[i];
    }
    printf("%d\\n", total);
    return 0;
}"""
    },
    "inefficient_malloc": {
        "title": "Repeated Heap Allocation in Loop",
        "code": """#include <stdio.h>
#include <stdlib.h>

void process_data(int n) {
    for (int i = 0; i < n; i++) {
        int* buffer = (int*)malloc(1024 * sizeof(int));
        buffer[0] = i * 2;
        /* Redundant heap churn on every iteration */
        free(buffer);
    }
}"""
    },
    "clean_binary_search": {
        "title": "Binary Search (Clean O(log N))",
        "code": """int binary_search(int arr[], int n, int target) {
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}"""
    },
    "inefficient_redundant_expr": {
        "title": "Duplicated Arithmetic Sub-Expressions",
        "code": """int calculate_weights(int a, int b, int n) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        total += (a * b + 42) * (i + 1);
        total += (a * b + 42) * (i + 1); /* Exact duplicate recomputation */
    }
    return total;
}"""
    }
}

def load_model_bundle():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)

@app.route("/")
def index():
    metrics = {}
    if METRICS_PATH.exists():
        try:
            metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except Exception:
            metrics = {}
    return render_template("index.html", metrics=metrics, presets=PRESETS)

@app.route("/api/scan", methods=["POST"])
def scan_code():
    data = request.get_json() or {}
    source = data.get("code", "")
    threshold = float(data.get("threshold", 0.60))

    if not source.strip():
        return jsonify({"error": "Source code cannot be empty"}), 400

    bundle = load_model_bundle()
    if not bundle:
        return jsonify({"error": "Trained model not found. Run python train_model.py first."}), 500

    model = bundle["model"]
    features = extract_features(source)
    feature_row = [features[name] for name in FEATURE_NAMES]
    X = pd.DataFrame([feature_row], columns=FEATURE_NAMES)

    raw_prediction = int(model.predict(X)[0])
    prob_classes = list(model.classes_)
    ineff_index = prob_classes.index(1) if 1 in prob_classes else 1
    probability = float(model.predict_proba(X)[0][ineff_index])

    is_inefficient = (raw_prediction == 1 and probability >= threshold)
    evidence = heuristic_evidence(source)

    # Specific refactoring guidance based on detected patterns
    recommendations = []
    if features.get("costly_loop_call_count", 0) > 0:
        recommendations.append("Hoist invariant function calls (like strlen or sqrt) outside of loop bounds to prevent redundant re-evaluations.")
    if features.get("allocation_keyword_count", 0) > 0 and features.get("loop_count", 0) > 0:
        recommendations.append("Consider allocating buffers once before loop execution and reusing them across iterations.")
    if features.get("repeated_expression_count", 0) > 0:
        recommendations.append("Store duplicated arithmetic calculations in a local const variable to enable better compiler register allocation.")
    if features.get("max_loop_nesting", 0) >= 3:
        recommendations.append("High loop nesting depth detected; evaluate algorithmic refactoring (e.g. hash lookups) to reduce polynomial time.")

    if not recommendations:
        if is_inefficient:
            recommendations.append("Review loop bodies and conditional structures for performance bottlenecks.")
        else:
            recommendations.append("Code adheres to standard static efficiency guidelines. Continue with unit tests and profiling.")

    return jsonify({
        "prediction": "POTENTIALLY INEFFICIENT" if is_inefficient else "POTENTIALLY SUFFICIENT / CLEAN",
        "is_inefficient": is_inefficient,
        "probability": round(probability, 4),
        "risk_percentage": round(probability * 100, 1),
        "threshold_percentage": round(threshold * 100, 1),
        "features": features,
        "evidence": evidence,
        "recommendations": recommendations,
        "feature_names": FEATURE_NAMES
    })

@app.route("/api/sample/<key>", methods=["GET"])
def get_sample(key):
    preset = PRESETS.get(key)
    if not preset:
        return jsonify({"error": "Preset not found"}), 404
    return jsonify(preset)

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    if METRICS_PATH.exists():
        return METRICS_PATH.read_text(encoding="utf-8"), 200, {"Content-Type": "application/json"}
    return jsonify({"error": "Metrics not found"}), 404

if __name__ == "__main__":
    print("Starting ML Inefficient Code Detector Web Studio at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
