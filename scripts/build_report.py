"""Assemble the final demo report from the training run, live results/
timeseries pulls, and the bulk traffic log. Saves both a timestamped JSON
and a human-readable summary to results/.

Usage: python scripts/build_report.py
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"


def load_latencies():
    latencies = []
    with open(RESULTS_DIR / "traffic_log.csv") as f:
        for row in csv.DictReader(f):
            latencies.append(float(row["latency_ms"]))
    return np.array(latencies)


def main():
    final_results = json.load(open("/tmp/final_results.json"))
    final_timeseries = json.load(open("/tmp/final_timeseries.json"))
    lat = load_latencies()

    training_accuracy = {
        "model_a_nb_baseline": 0.9830,
        "model_b_tfidf_logreg": 0.9803,
        "gap_b_minus_a": 0.9803 - 0.9830,
    }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "name": "SMS Spam Collection (UCI)",
            "total_messages": 5572,
            "train_size": 4457,
            "test_size": 1115,
        },
        "training": training_accuracy,
        "experiment_results": final_results,
        "timeseries_buckets": len(final_timeseries["buckets"]),
        "timeseries_first_bucket": final_timeseries["buckets"][0],
        "timeseries_last_bucket": final_timeseries["buckets"][-1],
        "predict_latency_ms": {
            "n": len(lat),
            "mean": round(float(lat.mean()), 2),
            "p50": round(float(np.percentile(lat, 50)), 2),
            "p95": round(float(np.percentile(lat, 95)), 2),
            "p99": round(float(np.percentile(lat, 99)), 2),
            "max": round(float(lat.max()), 2),
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = RESULTS_DIR / f"spam_ab_demo_report_{ts}.json"
    json_path.write_text(json.dumps(report, indent=2))

    summary_lines = [
        "KRISIS SPAM A/B DEMO — FINAL REPORT",
        f"Generated: {report['generated_at']}",
        "",
        "DATASET: SMS Spam Collection (UCI), 5572 messages, 4457 train / 1115 test (80/20 stratified)",
        "",
        "TRAINING (held-out test set):",
        f"  Model A (keyword-count + MultinomialNB):  accuracy = {training_accuracy['model_a_nb_baseline']:.4f}",
        f"  Model B (TF-IDF + LogisticRegression):     accuracy = {training_accuracy['model_b_tfidf_logreg']:.4f}",
        f"  Gap (B - A):                                {training_accuracy['gap_b_minus_a']:+.4f}",
        "",
        "LIVE EXPERIMENT RESULTS (/api/v1/experiments/spam_ab_demo/results):",
        f"  sample_size_a={final_results['sample_size_a']}  sample_size_b={final_results['sample_size_b']}",
        f"  model_a_mean={final_results['model_a_mean']}  model_b_mean={final_results['model_b_mean']}",
        f"  difference(B-A)={final_results['difference']}",
        f"  95% CI={final_results['confidence_interval']}  (excludes zero: {final_results['confidence_interval'][0] > 0 or final_results['confidence_interval'][1] < 0})",
        f"  warnings={final_results['warnings']}",
        "",
        "TIMESERIES CONVERGENCE:",
        f"  buckets={len(final_timeseries['buckets'])}",
        f"  first: {final_timeseries['buckets'][0]}",
        f"  last:  {final_timeseries['buckets'][-1]}",
        "",
        "PREDICT LATENCY (bulk run, n={}):".format(len(lat)),
        f"  mean={report['predict_latency_ms']['mean']}ms  p50={report['predict_latency_ms']['p50']}ms  "
        f"p95={report['predict_latency_ms']['p95']}ms  p99={report['predict_latency_ms']['p99']}ms  "
        f"max={report['predict_latency_ms']['max']}ms",
    ]
    summary_path = RESULTS_DIR / f"spam_ab_demo_summary_{ts}.txt"
    summary_path.write_text("\n".join(summary_lines))

    print(f"Saved {json_path}")
    print(f"Saved {summary_path}")
    print()
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
