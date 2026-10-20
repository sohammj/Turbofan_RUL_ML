"""Post-hoc engine-wise validation stability check using training trajectories only."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from src.cmapss_pipeline import DATASET_IDS, attach_train_rul, read_cmapss
from train_models import SEED, choose_sensors, feature_names, make_features, metrics, models


FRACTIONS = (0.50, 0.70, 0.85)
REPEATS = 3


def partial_endpoints(frame: pd.DataFrame) -> pd.DataFrame:
    """Return three non-terminal, reproducible rows for each held-out engine."""
    chosen = []
    for _, unit in frame.groupby("unit_id", sort=True):
        final_cycle = int(unit["cycle"].max())
        for fraction in FRACTIONS:
            endpoint = min(final_cycle - 1, max(1, int(final_cycle * fraction)))
            chosen.append(unit.loc[unit["cycle"] == endpoint].iloc[-1])
    return pd.DataFrame(chosen).reset_index(drop=True)


def evaluate_subset(root: Path, dataset_id: str) -> tuple[list[dict], list[dict]]:
    raw = read_cmapss(root / "data" / "raw" / "files" / f"train_{dataset_id}.txt")
    labeled = attach_train_rul(raw)
    splitter = GroupShuffleSplit(n_splits=REPEATS, test_size=0.20, random_state=SEED)
    result_rows = []
    split_records = []
    for repeat, (fit_idx, val_idx) in enumerate(
        splitter.split(labeled, groups=labeled["unit_id"]), start=1
    ):
        fit = labeled.iloc[fit_idx].copy()
        validation = labeled.iloc[val_idx].copy()
        fit_ids = set(fit["unit_id"])
        validation_ids = set(validation["unit_id"])
        if fit_ids & validation_ids:
            raise AssertionError("An engine appears in fitting and validation")
        sensors = choose_sensors(fit)
        features = feature_names(sensors)
        fit_features = make_features(fit, sensors)
        endpoints = partial_endpoints(make_features(validation, sensors))
        x_fit, y_fit = fit_features[features], fit_features["RUL"].to_numpy()
        x_val, y_val = endpoints[features], endpoints["RUL"].to_numpy()
        scores = []
        for name, model in models().items():
            model.fit(x_fit, y_fit)
            prediction = np.maximum(0.0, model.predict(x_val))
            score = metrics(y_val, prediction)
            row = {
                "dataset_id": dataset_id,
                "repeat": repeat,
                "model": name,
                "validation_engines": len(validation_ids),
                "validation_endpoints": len(endpoints),
                **score,
            }
            result_rows.append(row)
            scores.append(row)
        winner = min(scores, key=lambda row: (row["rmse"], row["mae"]))["model"]
        split_records.append({
            "dataset_id": dataset_id,
            "repeat": repeat,
            "fit_engine_count": len(fit_ids),
            "validation_engine_ids": sorted(int(unit) for unit in validation_ids),
            "selected_model": winner,
        })
        print(f"  repeat {repeat}: {winner}", flush=True)
    return result_rows, split_records


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "reports" / "robustness"
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    records = []
    for dataset_id in DATASET_IDS:
        print(dataset_id, flush=True)
        subset_rows, subset_records = evaluate_subset(root, dataset_id)
        rows.extend(subset_rows)
        records.extend(subset_records)
    results = pd.DataFrame(rows)
    results.to_csv(output / "repeated_validation_metrics.csv", index=False)
    summary = (results.groupby(["dataset_id", "model"], as_index=False)
               .agg(mean_rmse=("rmse", "mean"), std_rmse=("rmse", "std"),
                    mean_mae=("mae", "mean"), mean_r2=("r2", "mean")))
    summary.to_csv(output / "repeated_validation_summary.csv", index=False)
    winner_counts = (pd.DataFrame(records).groupby(["dataset_id", "selected_model"], as_index=False)
                     .size().rename(columns={"size": "wins_out_of_three"}))
    winner_counts.to_csv(output / "winner_counts.csv", index=False)
    (output / "split_protocol.json").write_text(json.dumps({
        "purpose": "Post-hoc stability audit of the existing candidates, not official test tuning",
        "source": "NASA training trajectories only; no official test RUL files read",
        "splitter": "GroupShuffleSplit",
        "random_state": SEED,
        "repeats": REPEATS,
        "validation_fraction": 0.20,
        "endpoint_fractions": list(FRACTIONS),
        "splits": records,
    }, indent=2) + "\n")

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    for ax, dataset_id in zip(axes.flat, DATASET_IDS):
        subset = summary.loc[summary["dataset_id"] == dataset_id]
        labels = subset["model"].str.replace("_", " ", regex=False)
        ax.barh(labels, subset["mean_rmse"], xerr=subset["std_rmse"], color="#527A9F")
        ax.set_title(dataset_id)
        ax.set_xlabel("Validation RMSE (cycles)")
    fig.suptitle("Three engine-wise validation splits per subset")
    fig.tight_layout()
    fig.savefig(output / "repeated_validation_rmse.png", dpi=160)
    plt.close(fig)
    print("Wrote", output)


if __name__ == "__main__":
    main()
