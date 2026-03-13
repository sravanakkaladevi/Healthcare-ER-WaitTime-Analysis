def to_decimal(value: float) -> str:
    """Formats a float to 4 decimal places."""
    return f"{value:.4f}"
def to_percentage(value: float) -> str:
    """Converts a float to a percentage string."""
    return f"{value * 100:.2f}%"
import argparse
import csv
import math
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path


from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


DATE_FORMAT = "%d-%m-%Y %H:%M"


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate predictive performance on the hospital ER dataset."
    )
    parser.add_argument(
        "--csv",
        default="Dataset/Hospital ER_Data.csv",
        help="Path to the ER dataset CSV file.",
    )
    return parser.parse_args()


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, DATE_FORMAT)


def build_classification_features(row: dict[str, str]) -> dict[str, object]:
    admitted_at = parse_datetime(row["Patient Admission Date"])
    satisfaction = row["Patient Satisfaction Score"].strip()

    return {
        "age": int(row["Patient Age"]),
        "gender": row["Patient Gender"],
        "race": row["Patient Race"],
        "department": row["Department Referral"],
        "visit_month": admitted_at.month,
        "visit_weekday": admitted_at.weekday(),
        "visit_hour": admitted_at.hour,
        "satisfaction_missing": int(not satisfaction),
        "satisfaction_score": int(satisfaction) if satisfaction else -1,
    }


def build_regression_features(row: dict[str, str]) -> dict[str, object]:
    admitted_at = parse_datetime(row["Patient Admission Date"])
    satisfaction = row["Patient Satisfaction Score"].strip()

    return {
        "age": int(row["Patient Age"]),
        "gender": row["Patient Gender"],
        "race": row["Patient Race"],
        "department": row["Department Referral"],
        "admission_flag": row["Patient Admission Flag"],
        "visit_month": admitted_at.month,
        "visit_weekday": admitted_at.weekday(),
        "visit_hour": admitted_at.hour,
        "satisfaction_missing": int(not satisfaction),
        "satisfaction_score": int(satisfaction) if satisfaction else -1,
    }


def evaluate_classification(rows: list[dict[str, str]]) -> dict[str, float]:
    features = [build_classification_features(row) for row in rows]
    labels = [1 if row["Patient Admission Flag"] == "TRUE" else 0 for row in rows]

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    vectorizer = DictVectorizer(sparse=False)
    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)

    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(x_train_vec, y_train)
    baseline_predictions = baseline.predict(x_test_vec)

    model = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=1,
    )
    model.fit(x_train_vec, y_train)
    predictions = model.predict(x_test_vec)

    return {
        "baseline_accuracy": accuracy_score(y_test, baseline_predictions),
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions),
        "recall": recall_score(y_test, predictions),
        "f1": f1_score(y_test, predictions),
    }


def evaluate_regression(rows: list[dict[str, str]]) -> dict[str, float]:
    features = [build_regression_features(row) for row in rows]
    labels = [float(row["Patient Waittime"]) for row in rows]

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
    )

    vectorizer = DictVectorizer(sparse=False)
    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)

    baseline = DummyRegressor(strategy="mean")
    baseline.fit(x_train_vec, y_train)
    baseline_predictions = baseline.predict(x_test_vec)

    model = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=1,
    )
    model.fit(x_train_vec, y_train)
    predictions = model.predict(x_test_vec)

    return {
        "baseline_mae": mean_absolute_error(y_test, baseline_predictions),
        "baseline_rmse": math.sqrt(mean_squared_error(y_test, baseline_predictions)),
        "mae": mean_absolute_error(y_test, predictions),
        "rmse": math.sqrt(mean_squared_error(y_test, predictions)),
        "r2": r2_score(y_test, predictions),
    }


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)

    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    rows = load_rows(csv_path)
    classification_metrics = evaluate_classification(rows)
    regression_metrics = evaluate_regression(rows)

    print(f"Rows evaluated: {len(rows)}")
    print()
    print("Admission prediction (classification)")
    print(
        f"  Baseline accuracy: {format_percent(classification_metrics['baseline_accuracy'])}"
    )
    print(f"  Accuracy:          {format_percent(classification_metrics['accuracy'])}")
    print(f"  Precision:         {format_percent(classification_metrics['precision'])}")
    print(f"  Recall:            {format_percent(classification_metrics['recall'])}")
    print(f"  F1 score:          {format_percent(classification_metrics['f1'])}")
    print()
    print("Wait time prediction (regression)")
    print(f"  Baseline MAE:      {regression_metrics['baseline_mae']:.2f} minutes")
    print(f"  Baseline RMSE:     {regression_metrics['baseline_rmse']:.2f} minutes")
    print(f"  MAE:               {regression_metrics['mae']:.2f} minutes")
    print(f"  RMSE:              {regression_metrics['rmse']:.2f} minutes")
    print(f"  R^2:               {format_percent(regression_metrics['r2'])}")


if __name__ == "__main__":
    main()
