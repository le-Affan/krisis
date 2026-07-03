"""Bulk traffic simulation: replay held-out test-set examples through a live
Krisis experiment via real HTTP calls.

For each example:
  1. POST /predict with the real SMS text -> real registered model runs,
     variant + prediction + latency recorded.
  2. Short artificial delay (simulates a real deployment where the true
     outcome isn't known until some time after the prediction was served —
     e.g. a user's later action, a manual review, a downstream event).
  3. POST /outcomes with 1 if the model's prediction matched the true label,
     0 otherwise. This is the "did the model get it right" metric the
     experiment compares between variants.

Saves a per-request log to results/traffic_log.csv (request_id, variant,
latency_ms, correct) for the final report script to compute latency
percentiles and other summaries from.

Usage: python scripts/simulate_traffic.py [--n 1000] [--experiment-id spam_ab_demo] [--base-url http://localhost:8150]
"""

import argparse
import csv
import random
import time
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"

# Texts already used in the manual sanity pass — excluded here so the bulk
# run doesn't double-count the same examples.
MANUAL_PASS_TEXTS = {
    "You have won ?1,000 cash or a ?2,000 prize! To claim, call09050000327",
    "You are now unsubscribed all services. Get tons of sexy babes or hunks straight to your phone! go to http://gotbabes.co.uk. No subscriptions.",
    "Wanna get laid 2nite? Want real Dogging locations sent direct to ur mobile? Join the UK's largest Dogging Network. Txt PARK to 69696 now! Nyt. ec2a. 3lp Â£1.50/msg",
    "Do you want 750 anytime any network mins 150 text and a NEW video phone for only five pounds per week call 08000776320 now or reply for delivery Tomorrow",
    "No need to buy lunch for me.. I eat maggi mee..",
    "Ok im not sure what time i finish tomorrow but i wanna spend the evening with you cos that would be vewy vewy lubly! Love me xxx",
    "Waiting in e car 4 my mum lor. U leh? Reach home already?",
    "If you r @ home then come down within 5 min",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000, help="number of examples to run")
    parser.add_argument("--experiment-id", default="spam_ab_demo")
    parser.add_argument("--base-url", default="http://localhost:8150")
    parser.add_argument("--outcome-delay-seconds", type=float, default=0.02)
    args = parser.parse_args()

    df = pd.read_csv(DATA_DIR / "test_set.csv")
    df = df[~df["text"].isin(MANUAL_PASS_TEXTS)].reset_index(drop=True)
    df = df.sample(n=min(args.n, len(df)), random_state=42).reset_index(drop=True)
    print(f"Replaying {len(df)} held-out test examples through {args.base_url}")

    RESULTS_DIR.mkdir(exist_ok=True)
    log_path = RESULTS_DIR / "traffic_log.csv"

    per_variant_count = {"A": 0, "B": 0}
    correct_count = {"A": 0, "B": 0}
    latencies_ms = []
    errors = 0

    with open(log_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["request_id", "variant", "latency_ms", "predicted", "true_label", "correct"])

        start = time.time()
        for i, row in df.iterrows():
            t0 = time.perf_counter()
            try:
                resp = requests.post(
                    f"{args.base_url}/api/v1/predict",
                    json={"experiment_id": args.experiment_id, "features": {"text": row["text"]}},
                    timeout=10,
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                errors += 1
                print(f"  [{i}] predict failed: {e}")
                continue
            latency_ms = (time.perf_counter() - t0) * 1000

            body = resp.json()
            request_id = body["request_id"]
            variant = body["model_variant"]
            prediction = body["prediction"]
            true_label = int(row["label"])
            correct = 1 if prediction == true_label else 0

            per_variant_count[variant] += 1
            correct_count[variant] += correct
            latencies_ms.append(latency_ms)

            # simulate delayed outcome reporting (e.g. a downstream event
            # arriving some time after the prediction was served)
            time.sleep(args.outcome_delay_seconds)

            requests.post(
                f"{args.base_url}/api/v1/outcomes",
                json={"request_id": request_id, "value": correct},
                timeout=10,
            )

            writer.writerow([request_id, variant, f"{latency_ms:.3f}", prediction, true_label, correct])

            if (i + 1) % 100 == 0:
                print(f"  {i + 1}/{len(df)} done...")

        elapsed = time.time() - start

    print("\n" + "=" * 60)
    print(f"Bulk run complete: {len(df)} requests, {errors} errors, {elapsed:.1f}s total")
    print(f"Per-variant sample size: A={per_variant_count['A']} B={per_variant_count['B']}")
    if per_variant_count["A"]:
        print(f"Variant A accuracy (this batch): {correct_count['A'] / per_variant_count['A']:.4f}")
    if per_variant_count["B"]:
        print(f"Variant B accuracy (this batch): {correct_count['B'] / per_variant_count['B']:.4f}")
    print(f"Log saved to {log_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
