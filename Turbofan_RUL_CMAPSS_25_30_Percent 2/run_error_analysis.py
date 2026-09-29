"""Summarize RUL errors from the fixed official test predictions."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.cmapss_pipeline import DATASET_IDS


def main() -> None:
    root = Path(__file__).resolve().parent
    modeling = root / "reports" / "modeling"
    frames = [pd.read_csv(modeling / dataset_id / "official_test_predictions.csv")
              for dataset_id in DATASET_IDS]
    data = pd.concat(frames, ignore_index=True)
    data["absolute_error"] = (data["predicted_rul"] - data["actual_rul"]).abs()
    data["error_direction"] = np.where(
        data["predicted_rul"] > data["actual_rul"],
        "overestimated_life",
        np.where(data["predicted_rul"] < data["actual_rul"], "underestimated_life", "exact"),
    )
    bins = [-1, 25, 50, 100, 150, np.inf]
    labels = ["0–25", "26–50", "51–100", "101–150", ">150"]
    data["actual_rul_band"] = pd.cut(data["actual_rul"], bins=bins, labels=labels)
    by_band = (data.groupby(["dataset_id", "actual_rul_band"], observed=True)
               .agg(engines=("unit_id", "size"), mae=("absolute_error", "mean"),
                    mean_signed_error=("error_predicted_minus_actual", "mean"))
               .reset_index())
    by_band.to_csv(modeling / "error_by_rul_band.csv", index=False)
    direction = (data.groupby(["dataset_id", "error_direction"], observed=True)
                 .size().rename("engines").reset_index())
    direction.to_csv(modeling / "error_direction_counts.csv", index=False)
    worst = data.sort_values("absolute_error", ascending=False).head(20)
    worst.to_csv(modeling / "largest_official_test_errors.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for dataset_id, group in by_band.groupby("dataset_id"):
        ax.plot(group["actual_rul_band"].astype(str), group["mae"], marker="o", label=dataset_id)
    ax.set(xlabel="Actual RUL band (cycles)", ylabel="Mean absolute error (cycles)",
           title="Official test error by true remaining life")
    ax.legend()
    fig.tight_layout()
    fig.savefig(modeling / "error_by_rul_band.png", dpi=160)
    plt.close(fig)
    print("Error-analysis outputs written to", modeling)


if __name__ == "__main__":
    main()
