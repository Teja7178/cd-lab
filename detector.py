"""Command-line detector for potentially inefficient source-code patterns."""
from pathlib import Path
import argparse
import sys
import joblib
import pandas as pd
from feature_extractor import FEATURE_NAMES, extract_features, heuristic_evidence

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "inefficient_code_model.joblib"

def main():
    parser = argparse.ArgumentParser(
        description="ML-assisted static scanner for potentially inefficient code patterns."
    )
    parser.add_argument(
        "source_file",
        nargs="?",
        default=str(ROOT / "examples" / "sample_inefficient.c"),
        help="Path to a source file to scan (default: examples/sample_inefficient.c)"
    )
    parser.add_argument("--threshold", type=float, default=0.60,
                        help="Minimum predicted probability to emit the ML warning (default: 0.60)")
    args = parser.parse_args()
    source_path = Path(args.source_file)
    if not source_path.exists():
        print(f"Error: file not found: {source_path}", file=sys.stderr)
        raise SystemExit(2)
    if not MODEL_PATH.exists():
        print("Model not found. Run `python train_model.py` first.", file=sys.stderr)
        raise SystemExit(2)
    source = source_path.read_text(encoding="utf-8", errors="replace")
    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    features = extract_features(source)
    X = pd.DataFrame([[features[name] for name in FEATURE_NAMES]], columns=FEATURE_NAMES)
    prediction = int(model.predict(X)[0])
    probability = float(model.predict_proba(X)[0][list(model.classes_).index(1)])
    is_inefficient = (prediction == 1 and probability >= args.threshold)
    result_str = (
        "POTENTIALLY INEFFICIENT (CODE SMELL DETECTED)"
        if is_inefficient
        else "POTENTIALLY SUFFICIENT / CLEAN (NO HIGH-CONFIDENCE SMELL)"
    )
    print("=" * 68)
    print("ML-BASED INEFFICIENT CODE PATTERN DETECTOR")
    print("=" * 68)
    print(f"File: {source_path}")
    print(f"Prediction: {result_str}")
    print(f"Inefficiency Risk Probability: {probability * 100:.1f}% (Threshold: {args.threshold * 100:.0f}%)")
    print("\nExtracted features:")
    for name, value in features.items():
        print(f"  {name}: {value:g}")
    print("\nStatic-analysis evidence:")
    for item in heuristic_evidence(source):
        print(f"  - {item}")
    print("\nInterpretation: this is a prototype prediction, not proof of a performance defect.")
    print("Confirm with code review, tests and profiling before changing the program.")

if __name__ == "__main__":
    main()
