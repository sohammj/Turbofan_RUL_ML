"""Train and evaluate classical RUL models with engine-wise validation."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.cmapss_pipeline import (
    DATASET_IDS,
    SENSOR_COLUMNS,
    SETTING_COLUMNS,
    TEMPORAL_SENSOR_CANDIDATES,
    attach_train_rul,
    read_cmapss,
    read_official_test_rul,
)

SEED = 42


def choose_sensors(train: pd.DataFrame) -> list[str]:
    retained = []
    for sensor in SENSOR_COLUMNS:
        counts = train[sensor].value_counts(normalize=True)
        if train[sensor].nunique() > 1 and float(counts.iloc[0]) < 0.95:
            retained.append(sensor)
    return retained


def make_features(frame: pd.DataFrame, sensors: list[str]) -> pd.DataFrame:
    out = frame.sort_values(["unit_id", "cycle"]).copy()
    for sensor in TEMPORAL_SENSOR_CANDIDATES:
        if sensor not in sensors:
            continue
        grouped = out.groupby("unit_id", sort=False)[sensor]
        out[f"{sensor}_delta_1"] = grouped.diff().fillna(0.0)
        out[f"{sensor}_rolling_mean_5"] = grouped.transform(
            lambda values: values.rolling(5, min_periods=1).mean()
        )
    return out


def feature_names(sensors: list[str]) -> list[str]:
    names = ["cycle"] + SETTING_COLUMNS + sensors
    for sensor in TEMPORAL_SENSOR_CANDIDATES:
        if sensor in sensors:
            names.extend([f"{sensor}_delta_1", f"{sensor}_rolling_mean_5"])
    return names


def validation_endpoints(frame: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """Choose one reproducible partial-history endpoint per held-out engine."""
    rng = np.random.default_rng(seed)
    selected = []
    for _, unit in frame.groupby("unit_id", sort=True):
        final_cycle = int(unit["cycle"].max())
        fraction = float(rng.uniform(0.50, 0.85))
        endpoint = min(final_cycle - 1, max(1, int(final_cycle * fraction)))
        selected.append(unit.loc[unit["cycle"] == endpoint].iloc[-1])
    return pd.DataFrame(selected).reset_index(drop=True)


def phm_score(actual: np.ndarray, predicted: np.ndarray) -> float:
    error = np.asarray(predicted, dtype=float) - np.asarray(actual, dtype=float)
    return float(np.where(error < 0, np.expm1(-error / 13), np.expm1(error / 10)).sum())


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    actual = np.asarray(actual, dtype=float)
    predicted = np.maximum(0.0, np.asarray(predicted, dtype=float))
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
        "phm_score": phm_score(actual, predicted),
    }


def models() -> dict:
    return {
        "median_baseline": DummyRegressor(strategy="median"),
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
        "random_forest": RandomForestRegressor(
            n_estimators=80, min_samples_leaf=4, max_features=0.8,
            n_jobs=-1, random_state=SEED,
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=150, max_leaf_nodes=31, l2_regularization=1.0,
            random_state=SEED,
        ),
    }


def save_scatter(path: Path, actual: np.ndarray, predicted: np.ndarray, title: str) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.scatter(actual, predicted, alpha=0.7, s=24)
    bound = max(float(np.max(actual)), float(np.max(predicted))) * 1.05
    ax.plot([0, bound], [0, bound], color="black", linestyle="--", linewidth=1)
    ax.set(xlabel="Actual RUL (cycles)", ylabel="Predicted RUL (cycles)", title=title,
           xlim=(0, bound), ylim=(0, bound))
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run_subset(root: Path, dataset_id: str) -> dict:
    raw = root / "data" / "raw" / "files"
    out = root / "reports" / "modeling" / dataset_id
    out.mkdir(parents=True, exist_ok=True)
    train_raw = read_cmapss(raw / f"train_{dataset_id}.txt")
    test_raw = read_cmapss(raw / f"test_{dataset_id}.txt")
    train_labeled = attach_train_rul(train_raw)

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SEED)
    fit_idx, validation_idx = next(
        splitter.split(train_labeled, groups=train_labeled["unit_id"])
    )
    fit_raw = train_labeled.iloc[fit_idx].copy()
    validation_raw = train_labeled.iloc[validation_idx].copy()
    fit_ids = set(fit_raw["unit_id"])
    validation_ids = set(validation_raw["unit_id"])
    if fit_ids & validation_ids:
        raise AssertionError("An engine appears in both fitting and validation sets")

    sensors = choose_sensors(fit_raw)
    features = feature_names(sensors)
    fit = make_features(fit_raw, sensors)
    validation = validation_endpoints(make_features(validation_raw, sensors))
    X_fit = fit[features]
    y_fit = fit["RUL"].to_numpy()
    X_validation = validation[features]
    y_validation = validation["RUL"].to_numpy()
    rows = []
    for name, model in models().items():
        model.fit(X_fit, y_fit)
        prediction = np.maximum(0.0, model.predict(X_validation))
        rows.append({"dataset_id": dataset_id, "model": name, "split": "validation",
                     "engines": len(validation_ids), **metrics(y_validation, prediction)})
    results = pd.DataFrame(rows).sort_values(["rmse", "mae"])
    results.to_csv(out / "validation_metrics.csv", index=False)
    winner = str(results.iloc[0]["model"])

    full_sensors = choose_sensors(train_labeled)
    full_features = feature_names(full_sensors)
    full_train = make_features(train_labeled, full_sensors)
    test = make_features(test_raw, full_sensors)
    last_test = test.loc[test.groupby("unit_id")["cycle"].idxmax()].sort_values("unit_id")
    official = read_official_test_rul(raw / f"RUL_{dataset_id}.txt").to_numpy()
    if len(last_test) != len(official):
        raise AssertionError("Official test RUL count does not match test engines")
    final_model = models()[winner]
    final_model.fit(full_train[full_features], full_train["RUL"])
    prediction = np.maximum(0.0, final_model.predict(last_test[full_features]))
    prediction_table = pd.DataFrame({
        "dataset_id": dataset_id,
        "unit_id": last_test["unit_id"].to_numpy(),
        "last_observed_cycle": last_test["cycle"].to_numpy(),
        "actual_rul": official,
        "predicted_rul": prediction.round(3),
        "error_predicted_minus_actual": (prediction - official).round(3),
    })
    prediction_table.to_csv(out / "official_test_predictions.csv", index=False)
    official_metrics = {"dataset_id": dataset_id, "model": winner, "split": "official_test",
                        "engines": len(official), **metrics(official, prediction)}
    pd.DataFrame([official_metrics]).to_csv(out / "official_test_metrics.csv", index=False)
    save_scatter(out / "official_test_actual_vs_predicted.png", official, prediction,
                 f"{dataset_id}: {winner} on official test")
    protocol = {
        "dataset_id": dataset_id,
        "random_seed": SEED,
        "validation_engine_ids": sorted(int(x) for x in validation_ids),
        "fit_engine_count": len(fit_ids),
        "validation_engine_count": len(validation_ids),
        "validation_endpoint_fraction_range": [0.50, 0.85],
        "selection_metric": "validation RMSE at one partial-history endpoint per held-out engine",
        "validation_retained_sensors": sensors,
        "full_training_retained_sensors": full_sensors,
        "selected_model": winner,
        "official_test_labels_used_for_model_selection": False,
    }
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    return official_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subsets", nargs="+", choices=DATASET_IDS, default=list(DATASET_IDS))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    summary = []
    for dataset_id in args.subsets:
        print(f"Training {dataset_id}...", flush=True)
        result = run_subset(root, dataset_id)
        summary.append(result)
        print(f"  {result['model']}: test MAE={result['mae']:.2f}, RMSE={result['rmse']:.2f}", flush=True)
    report_dir = root / "reports" / "modeling"
    pd.DataFrame(summary).to_csv(report_dir / "official_test_summary.csv", index=False)


if __name__ == "__main__":
    main()
