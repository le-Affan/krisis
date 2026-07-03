# Krisis Spam A/B Demo — Report

Real end-to-end run of Krisis against two independently trained spam classifiers, on a live local instance, over real HTTP. Raw source data: [`spam_ab_demo_report_20260703_000924.json`](spam_ab_demo_report_20260703_000924.json). Reproduce with `scripts/train_models.py` + `scripts/simulate_traffic.py` — see the README's "Reproduce the demo yourself" section for exact commands.

## Dataset

[SMS Spam Collection](https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip) (UCI), 5572 real labeled SMS messages (4825 ham / 747 spam). 80/20 stratified split: 4457 train, 1115 held-out test.

## Training (held-out test set)

| Model | Approach | Accuracy |
|---|---|---|
| A | keyword-count + Multinomial Naive Bayes | 0.9830 |
| B | TF-IDF + Logistic Regression | 0.9803 |
| Gap (B − A) | | **−0.0027** |

Model B did not beat Model A offline — Naive Bayes is a well-known strong baseline on this exact benchmark. B's hyperparameters were tuned via 5-fold CV on the training split only (no test-set leakage); the result held. Reported as-is rather than re-tuned until B won — the point of this demo is to show what the *online* A/B test does with a marginal, ambiguous offline gap like this one.

## Live experiment (`GET /api/v1/experiments/{id}/results`)

Krisis routed 1008 real predictions (8 from a manual sanity pass + 1000 from a bulk simulation) between the two registered models via 50/50 traffic split, scored each prediction against ground truth, and computed:

| | |
|---|---|
| sample_size_a | 512 |
| sample_size_b | 496 |
| model_a_mean (accuracy) | 0.9844 |
| model_b_mean (accuracy) | 0.9778 |
| difference (B − A) | −0.0066 |
| 95% CI | **[−0.0234, 0.0103]** — includes zero |
| guardrail warning | "High variance relative to effect size: pooled std 0.1361 > 2× observed difference 0.0066; confidence interval will be wide and unreliable" |

**The result:** the small offline accuracy gap (0.27pp) is statistically indistinguishable from zero at n≈500/variant. Krisis's own guardrail correctly flags this rather than reporting a false "B is worse." This is the actual value proposition — catching the difference between a real effect and noise before anyone ships a decision on it.

## Timeseries convergence (`GET /api/v1/experiments/{id}/timeseries`)

CI width narrows as sample size accumulates:

| bucket | n_a / n_b | CI | width |
|---|---|---|---|
| first | 4 / 4 | [0.0, 0.0] | 0 (degenerate, too few samples) |
| mid | 110 / 113 | [−0.0566, 0.0035] | 0.0601 |
| mid | 301 / 314 | [−0.0302, 0.0053] | 0.0355 |
| last | 512 / 496 | [−0.0234, 0.0103] | 0.0337 |

## `/predict` latency (bulk run, n=1000, in-process `python_callable` adapter)

| p50 | p95 | p99 | mean | max |
|---|---|---|---|---|
| 6.74ms | 7.75ms | 9.06ms | 6.87ms | 54.42ms |
