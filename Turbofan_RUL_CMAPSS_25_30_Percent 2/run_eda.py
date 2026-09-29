"""Reproduce the exploratory analysis from the untouched NASA text files."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.cmapss_pipeline import DATASET_IDS, SENSOR_COLUMNS, read_cmapss


def main() -> None:
    root = Path(__file__).resolve().parent
    raw = root / "data" / "raw" / "files"
    out = root / "reports" / "eda"
    out.mkdir(parents=True, exist_ok=True)
    lifetime_rows = []
    sensor_rows = []
    for dataset_id in DATASET_IDS:
        train = read_cmapss(raw / f"train_{dataset_id}.txt")
        test = read_cmapss(raw / f"test_{dataset_id}.txt")
        for split, frame in (("train", train), ("test", test)):
            lifetimes = frame.groupby("unit_id")["cycle"].max()
            lifetime_rows.append({
                "dataset_id": dataset_id,
                "split": split,
                "rows": len(frame),
                "engines": len(lifetimes),
                "cycle_min": int(lifetimes.min()),
                "cycle_median": float(lifetimes.median()),
                "cycle_mean": float(lifetimes.mean()),
                "cycle_max": int(lifetimes.max()),
            })
        for sensor in SENSOR_COLUMNS:
            sensor_rows.append({
                "dataset_id": dataset_id,
                "sensor": sensor,
                "unique_values": int(train[sensor].nunique()),
                "standard_deviation": float(train[sensor].std(ddof=0)),
            })

    lifetime_table = pd.DataFrame(lifetime_rows)
    sensor_table = pd.DataFrame(sensor_rows)
    lifetime_table.to_csv(out / "engine_lifetimes.csv", index=False)
    sensor_table.to_csv(out / "sensor_variation.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    for dataset_id in DATASET_IDS:
        train = read_cmapss(raw / f"train_{dataset_id}.txt")
        lives = train.groupby("unit_id")["cycle"].max()
        ax.hist(lives, bins=18, alpha=0.45, label=dataset_id)
    ax.set(title="Training-engine lifetimes by C-MAPSS subset", xlabel="Cycles to failure", ylabel="Engines")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "engine_lifetimes.png", dpi=160)
    plt.close(fig)

    train = read_cmapss(raw / "train_FD001.txt")
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)
    for unit_id in (1, 2, 3):
        unit = train.loc[train.unit_id == unit_id]
        for ax, sensor in zip(axes, ("sensor_2", "sensor_11")):
            ax.plot(unit.cycle, unit[sensor], label=f"Engine {unit_id}", linewidth=1.2)
    for ax, sensor in zip(axes, ("sensor_2", "sensor_11")):
        ax.set_ylabel(sensor)
        ax.legend(fontsize=8)
    axes[-1].set_xlabel("Operating cycle")
    fig.suptitle("Example FD001 sensor trajectories")
    fig.tight_layout()
    fig.savefig(out / "fd001_sensor_trajectories.png", dpi=160)
    plt.close(fig)

    lines = [
        "# Exploratory data analysis",
        "",
        "Run `python run_eda.py` from the project directory to reproduce the tables and figures in `reports/eda/`.",
        "",
        "The tables report per-subset engine lifetimes and training-sensor variation. The lifetime figure shows that engine histories have unequal lengths. The FD001 example plots show that sensor values vary by engine and cycle; they are illustrations, not proof that one sensor alone predicts failure.",
        "",
        "The data are simulated run-to-failure histories. Training rows contain complete trajectories; test histories stop earlier. All model comparisons must split by engine and avoid using future cycles as input.",
        "",
        "```text",
        lifetime_table.to_string(index=False),
        "```",
        "",
    ]
    (out / "EDA_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"EDA outputs: {out}")


if __name__ == "__main__":
    main()
