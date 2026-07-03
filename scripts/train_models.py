"""Download the SMS Spam Collection dataset, train two competing spam
classifiers (a weaker keyword-count+NB baseline as Model A, a stronger
TF-IDF+LogReg model as Model B), evaluate both on a held-out test set, and
save everything needed for the Krisis A/B demo.

Usage: python scripts/train_models.py
"""

import io
import zipfile
from pathlib import Path

import joblib
import pandas as pd
import requests
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
MODELS_DIR = REPO_ROOT / "models"

DATASET_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"
FALLBACK_URL = (
    "https://raw.githubusercontent.com/mohitgupta-omg/"
    "Kaggle-SMS-Spam-Collection-Dataset-/master/spam.csv"
)


def download_dataset() -> pd.DataFrame:
    DATA_DIR.mkdir(exist_ok=True)
    raw_path = DATA_DIR / "SMSSpamCollection"

    if not raw_path.exists():
        print(f"Downloading dataset from {DATASET_URL} ...")
        try:
            resp = requests.get(DATASET_URL, timeout=30)
            resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                zf.extractall(DATA_DIR)
            print(f"Extracted to {raw_path}")
        except Exception as e:
            print(f"Primary source failed ({e}), trying fallback mirror...")
            resp = requests.get(FALLBACK_URL, timeout=30)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text), encoding="latin-1")
            df = df.iloc[:, :2]
            df.columns = ["label", "text"]
            df.to_csv(DATA_DIR / "sms_spam.csv", index=False)
            print(f"Saved fallback dataset to {DATA_DIR / 'sms_spam.csv'}")
            return df

    df = pd.read_csv(raw_path, sep="\t", header=None, names=["label", "text"], encoding="latin-1")
    df.to_csv(DATA_DIR / "sms_spam.csv", index=False)
    return df


def main():
    df = download_dataset()
    print(f"\nDataset loaded: {len(df)} messages")
    print(df["label"].value_counts().to_string())

    X = df["text"]
    y = (df["label"] == "spam").astype(int)  # 1 = spam, 0 = ham

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"\nTrain: {len(X_train)}  Test: {len(X_test)}")
    print(f"Train spam rate: {y_train.mean():.4f}  Test spam rate: {y_test.mean():.4f}")

    # --- Model A: keyword-count + Multinomial Naive Bayes (weaker baseline) ---
    vectorizer_a = CountVectorizer(stop_words="english", max_features=1000)
    X_train_a = vectorizer_a.fit_transform(X_train)
    X_test_a = vectorizer_a.transform(X_test)

    model_a = MultinomialNB()
    model_a.fit(X_train_a, y_train)
    preds_a = model_a.predict(X_test_a)
    accuracy_a = accuracy_score(y_test, preds_a)

    # --- Model B: TF-IDF + Logistic Regression (stronger) ---
    # Hyperparameters chosen via 5-fold CV on the training split only
    # (max_features/ngram_range/C grid search; sublinear_tf is standard
    # practice for TF-IDF on short text) — not tuned against the test set.
    vectorizer_b = TfidfVectorizer(
        stop_words="english", max_features=5000, ngram_range=(1, 2), sublinear_tf=True
    )
    X_train_b = vectorizer_b.fit_transform(X_train)
    X_test_b = vectorizer_b.transform(X_test)

    model_b = LogisticRegression(max_iter=2000, C=50)
    model_b.fit(X_train_b, y_train)
    preds_b = model_b.predict(X_test_b)
    accuracy_b = accuracy_score(y_test, preds_b)

    print("\n" + "=" * 60)
    print(f"Model A (keyword-count + MultinomialNB):  accuracy = {accuracy_a:.4f}")
    print(f"Model B (TF-IDF + LogisticRegression):     accuracy = {accuracy_b:.4f}")
    print(f"Gap (B - A):                                {accuracy_b - accuracy_a:+.4f}")
    print("=" * 60)

    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump({"vectorizer": vectorizer_a, "model": model_a}, MODELS_DIR / "model_a.joblib")
    joblib.dump({"vectorizer": vectorizer_b, "model": model_b}, MODELS_DIR / "model_b.joblib")
    print(f"\nSaved model_a.joblib and model_b.joblib to {MODELS_DIR}/")

    # Save the held-out test set (with true labels) so the demo/simulation
    # scripts can replay real examples through Krisis without retraining.
    test_df = pd.DataFrame({"text": X_test, "label": y_test})
    test_df.to_csv(DATA_DIR / "test_set.csv", index=False)
    print(f"Saved held-out test set ({len(test_df)} rows) to {DATA_DIR / 'test_set.csv'}")


if __name__ == "__main__":
    main()
