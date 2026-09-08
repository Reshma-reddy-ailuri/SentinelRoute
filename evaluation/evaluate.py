import os
import sys
import json
import time
from pathlib import Path

# Add backend directory to sys.path so we can import detection & policy modules
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.detection.unified_detector import UnifiedDetector
from app.policy.policy_engine import PolicyEngine


def run_evaluation():
    print("=" * 80)
    print("  ENTERPRISE GenAI SECURITY GATEWAY — BENCHMARK EVALUATION SUITE")
    print("=" * 80)

    dataset_path = BASE_DIR / "evaluation" / "dataset" / "synthetic_dataset.json"
    if not dataset_path.exists():
        print(f"Error: Synthetic dataset file not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"Loaded {len(dataset)} synthetic test cases from dataset.")
    print("Initializing Multi-Layer Unified Detector & Policy Engine...\n")

    detector = UnifiedDetector()
    policy_engine = PolicyEngine()

    tp = 0  # True Positives: Sensitive prompt correctly BLOCKED
    tn = 0  # True Negatives: Safe prompt correctly ALLOWED
    fp = 0  # False Positives: Safe prompt incorrectly BLOCKED
    fn = 0  # False Negatives: Sensitive prompt incorrectly ALLOWED

    category_stats = {}
    latencies = []

    for item in dataset:
        prompt_id = item["id"]
        prompt = item["prompt"]
        expected_action = item["expected_action"]  # ALLOW or BLOCK
        category = item.get("category", "UNKNOWN")

        if category not in category_stats:
            category_stats[category] = {"total": 0, "correct": 0, "latencies": []}

        category_stats[category]["total"] += 1

        # Measure Security Gateway detection & policy evaluation latency ONLY (excluding network LLM)
        start_time = time.time()
        detection_res = detector.analyze(prompt)
        policy_res = policy_engine.evaluate(detection_res)
        gateway_latency_ms = (time.time() - start_time) * 1000

        latencies.append(gateway_latency_ms)
        category_stats[category]["latencies"].append(gateway_latency_ms)

        actual_action = policy_res["decision"]
        is_correct = (actual_action == expected_action)

        if is_correct:
            category_stats[category]["correct"] += 1

        # Confusion matrix logic (Sensitive/Blocked = Positive class)
        if expected_action == "BLOCK":  # Actual sensitive
            if actual_action == "BLOCK":
                tp += 1
            else:
                fn += 1
                print(f"[FAIL - False Negative] ID {prompt_id} ({category}): Sensitive prompt ALLOWED!")
                print(f"  Prompt: {prompt}\n")
        else:  # Actual safe
            if actual_action == "ALLOW":
                tn += 1
            else:
                fp += 1
                print(f"[FAIL - False Positive] ID {prompt_id} ({category}): Safe prompt BLOCKED!")
                print(f"  Prompt: {prompt}\n")

    total_samples = len(dataset)
    accuracy = ((tp + tn) / total_samples) * 100 if total_samples > 0 else 0.0
    precision = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    avg_gateway_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("-" * 80)
    print("                      OVERALL EVALUATION RESULTS")
    print("-" * 80)
    print(f"Total Test Prompts  : {total_samples}")
    print(f"True Positives (TP) : {tp:<4} (Sensitive prompts correctly BLOCKED)")
    print(f"True Negatives (TN) : {tn:<4} (Safe prompts correctly ALLOWED)")
    print(f"False Positives (FP): {fp:<4} (Safe prompts incorrectly BLOCKED)")
    print(f"False Negatives (FN): {fn:<4} (Sensitive prompts incorrectly ALLOWED)")
    print("-" * 80)
    print(f"Accuracy            : {accuracy:.2f}%")
    print(f"Precision           : {precision:.2f}%")
    print(f"Recall              : {recall:.2f}%")
    print(f"F1-Score            : {f1_score:.2f}%")
    print(f"Gateway Latency     : {avg_gateway_latency:.2f} ms (Detection + Policy Engine)")
    print(f"External LLM Latency: ~500 - 1500 ms (Observed when forwarded to Groq Cloud API)")
    print("-" * 80)

    print("\n" + "=" * 80)
    print("                 PER-CATEGORY PERFORMANCE BREAKDOWN")
    print("=" * 80)
    print(f"{'Category':<25} | {'Total':<6} | {'Accuracy':<10} | {'Gateway Latency (ms)':<20}")
    print("-" * 80)
    for cat, data in category_stats.items():
        cat_acc = (data["correct"] / data["total"]) * 100 if data["total"] > 0 else 0.0
        cat_lat = sum(data["latencies"]) / len(data["latencies"]) if data["latencies"] else 0.0
        print(f"{cat:<25} | {data['total']:<6} | {cat_acc:<9.2f}% | {cat_lat:<20.2f}")
    print("=" * 80)

    # Save summary report to JSON file for documentation
    report_file = BASE_DIR / "evaluation" / "evaluation_report.json"
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_prompts": total_samples,
        "metrics": {
            "accuracy_percent": round(accuracy, 2),
            "precision_percent": round(precision, 2),
            "recall_percent": round(recall, 2),
            "f1_score_percent": round(f1_score, 2),
            "avg_gateway_latency_ms": round(avg_gateway_latency, 2),
            "note_llm_latency": "External LLM API latency (~500-1500ms) occurs only for ALLOWED prompts"
        },
        "confusion_matrix": {
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn
        },
        "category_breakdown": category_stats
    }
    with open(report_file, "w", encoding="utf-8") as rf:
        json.dump(report_data, rf, indent=2)

    print(f"\nSaved evaluation report artifact to: {report_file}\n")


if __name__ == "__main__":
    run_evaluation()
