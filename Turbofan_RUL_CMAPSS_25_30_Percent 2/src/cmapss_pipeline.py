"""Reproducible preprocessing pipeline for NASA C-MAPSS FD001-FD004.

The pipeline preserves raw inputs, derives row-level RUL labels, audits data
quality, makes causal time-series features, fits scalers on training data only,
and exports subset-level and merged deliverables.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


DATASET_IDS = ("FD001", "FD002", "FD003", "FD004")
ID_COLUMNS = ["unit_id", "cycle"]
SETTING_COLUMNS = [f"op_setting_{i}" for i in range(1, 4)]
SENSOR_COLUMNS = [f"sensor_{i}" for i in range(1, 22)]
RAW_COLUMNS = ID_COLUMNS + SETTING_COLUMNS + SENSOR_COLUMNS
TEMPORAL_SENSOR_CANDIDATES = [
    "sensor_2", "sensor_3", "sensor_4", "sensor_7",
    "sensor_11", "sensor_12", "sensor_15", "sensor_21",
]
RUL_CAP = 125
NEAR_CONSTANT_DOMINANT_SHARE = 0.95


def read_cmapss(path: Path) -> pd.DataFrame:
    """Read one 26-column whitespace-delimited C-MAPSS trajectory file."""
    frame = pd.read_csv(path, sep=r"\s+", header=None)
    if frame.shape[1] != len(RAW_COLUMNS):
        raise ValueError(
            f"{path.name}: expected {len(RAW_COLUMNS)} columns, got {frame.shape[1]}"
        )
    frame.columns = RAW_COLUMNS
    frame[ID_COLUMNS] = frame[ID_COLUMNS].astype("int64")
    numeric = SETTING_COLUMNS + SENSOR_COLUMNS
    frame[numeric] = frame[numeric].astype("float64")
    return frame


def read_official_test_rul(path: Path) -> pd.Series:
    """Read the official RUL-at-last-observation vector."""
    values = pd.read_csv(path, sep=r"\s+", header=None).iloc[:, 0]
    if values.isna().any() or (values < 0).any():
        raise ValueError(f"{path.name}: RUL vector contains missing/negative values")
    return values.astype("int64").reset_index(drop=True)


def validate_engine_cycles(frame: pd.DataFrame, source_name: str) -> None:
    """Fail on duplicate engine-cycle keys or non-increasing/non-contiguous cycles."""
    duplicated_keys = int(frame.duplicated(ID_COLUMNS).sum())
    if duplicated_keys:
        raise ValueError(f"{source_name}: {duplicated_keys} duplicate engine-cycle keys")
    for unit_id, cycles in frame.groupby("unit_id", sort=True)["cycle"]:
        expected = np.arange(1, len(cycles) + 1)
        if not np.array_equal(cycles.to_numpy(), expected):
            raise ValueError(f"{source_name}: unit {unit_id} cycles are not contiguous from 1")


def attach_train_rul(frame: pd.DataFrame) -> pd.DataFrame:
    """RUL(cycle) = final training cycle for that unit - current cycle."""
    out = frame.copy()
    out["observed_last_cycle"] = out.groupby("unit_id")["cycle"].transform("max")
    out["true_failure_cycle"] = out["observed_last_cycle"]
    out["RUL"] = out["true_failure_cycle"] - out["cycle"]
    out["RUL_capped_125"] = out["RUL"].clip(upper=RUL_CAP)
    out["is_last_observation"] = out["cycle"].eq(out["observed_last_cycle"]).astype("int8")
    return out


def attach_test_rul(frame: pd.DataFrame, official_rul: pd.Series) -> pd.DataFrame:
    """Attach official test RUL correctly to every observed cycle.

    Official vector entry i is RUL after the last recorded cycle for engine i.
    Therefore row-level RUL = official terminal RUL + last observed cycle - row cycle.
    """
    out = frame.copy()
    unit_ids = sorted(out["unit_id"].unique().tolist())
    if unit_ids != list(range(1, len(unit_ids) + 1)):
        raise ValueError("Test unit IDs are not contiguous from 1; cannot map RUL vector safely")
    if len(official_rul) != len(unit_ids):
        raise ValueError(
            f"Test RUL vector has {len(official_rul)} entries for {len(unit_ids)} engines"
        )
    terminal_map = dict(zip(unit_ids, official_rul.tolist()))
    out["observed_last_cycle"] = out.groupby("unit_id")["cycle"].transform("max")
    out["rul_at_last_observation"] = out["unit_id"].map(terminal_map).astype("int64")
    out["true_failure_cycle"] = out["observed_last_cycle"] + out["rul_at_last_observation"]
    out["RUL"] = out["true_failure_cycle"] - out["cycle"]
    out["RUL_capped_125"] = out["RUL"].clip(upper=RUL_CAP)
    out["is_last_observation"] = out["cycle"].eq(out["observed_last_cycle"]).astype("int8")
    return out


def audit_quality(frame: pd.DataFrame, dataset_id: str, split: str) -> dict:
    return {
        "dataset_id": dataset_id,
        "split": split,
        "rows": int(len(frame)),
        "columns_raw": int(len(RAW_COLUMNS)),
        "engines": int(frame["unit_id"].nunique()),
        "minimum_cycle": int(frame["cycle"].min()),
        "maximum_observed_cycle": int(frame["cycle"].max()),
        "missing_cells": int(frame.isna().sum().sum()),
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "duplicate_engine_cycle_keys": int(frame.duplicated(ID_COLUMNS).sum()),
        "infinite_numeric_cells": int(
            np.isinf(frame.select_dtypes(include=[np.number]).to_numpy()).sum()
        ),
        "unit_id_dtype": str(frame["unit_id"].dtype),
        "cycle_dtype": str(frame["cycle"].dtype),
        "measurement_dtype": str(frame[SENSOR_COLUMNS[0]].dtype),
    }


def audit_sensors(train: pd.DataFrame, dataset_id: str) -> pd.DataFrame:
    rows = []
    for column in SENSOR_COLUMNS:
        counts = train[column].value_counts(dropna=False, normalize=True)
        unique_count = int(train[column].nunique(dropna=False))
        dominant_share = float(counts.iloc[0])
        exact_constant = unique_count == 1
        near_constant = (not exact_constant) and dominant_share >= NEAR_CONSTANT_DOMINANT_SHARE
        if exact_constant:
            decision = "drop_exact_constant"
            reason = "one unique training value; no within-subset predictive variation"
        elif near_constant:
            decision = "drop_near_constant"
            reason = (
                f"most common training value occupies {dominant_share:.2%} of rows "
                f"(threshold {NEAR_CONSTANT_DOMINANT_SHARE:.0%})"
            )
        else:
            decision = "retain"
            reason = "sufficient training variation under the declared rule"
        rows.append(
            {
                "dataset_id": dataset_id,
                "feature": column,
                "unique_values": unique_count,
                "dominant_value_share": dominant_share,
                "minimum": float(train[column].min()),
                "maximum": float(train[column].max()),
                "mean": float(train[column].mean()),
                "population_std": float(train[column].std(ddof=0)),
                "decision": decision,
                "reason": reason,
            }
        )
    return pd.DataFrame(rows)


def add_causal_temporal_features(
    frame: pd.DataFrame,
    available_sensors: Iterable[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Create current/past-only deltas and 5-cycle rolling means."""
    out = frame.sort_values(["dataset_id", "unit_id", "cycle"]).copy()
    temporal_columns: list[str] = []
    group_keys = ["dataset_id", "unit_id"]
    available = set(available_sensors)
    for sensor in TEMPORAL_SENSOR_CANDIDATES:
        if sensor not in available:
            continue
        delta_name = f"{sensor}_delta_1"
        mean_name = f"{sensor}_rolling_mean_5"
        grouped = out.groupby(group_keys, sort=False)[sensor]
        out[delta_name] = grouped.diff().fillna(0.0)
        out[mean_name] = grouped.transform(
            lambda values: values.rolling(window=5, min_periods=1).mean()
        )
        temporal_columns.extend([delta_name, mean_name])
    return out, temporal_columns


def fit_standardizer(train: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    records = []
    for column in columns:
        mean = float(train[column].mean())
        std = float(train[column].std(ddof=0))
        zero_variance = bool(np.isclose(std, 0.0))
        records.append(
            {
                "feature": column,
                "train_mean": mean,
                "train_population_std": std,
                "scale_used": 1.0 if zero_variance else std,
                "zero_variance_guard_applied": zero_variance,
            }
        )
    return pd.DataFrame(records)


def apply_standardizer(
    frame: pd.DataFrame,
    parameters: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    out = frame.copy()
    params = parameters.set_index("feature")
    for column in columns:
        out[column] = (
            out[column] - params.loc[column, "train_mean"]
        ) / params.loc[column, "scale_used"]
    return out


def model_ready_columns(feature_columns: list[str], split: str) -> list[str]:
    columns = ["dataset_id", "unit_id", "cycle"] + feature_columns
    columns += [
        "observed_last_cycle", "true_failure_cycle", "RUL", "RUL_capped_125",
        "is_last_observation",
    ]
    if split == "test":
        columns.insert(-3, "rul_at_last_observation")
    return columns


def save_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.8f")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for record in frame.astype(str).itertuples(index=False, name=None):
        rows.append("| " + " | ".join(str(value).replace("|", "\\|") for value in record) + " |")
    return "\n".join([header, separator] + rows)


def write_preprocessing_summary(
    project_root: Path,
    dataset_summary: pd.DataFrame,
    quality_summary: pd.DataFrame,
    feature_audit: pd.DataFrame,
    global_drop: list[str],
    temporal_columns: list[str],
) -> None:
    compact_dataset = dataset_summary[
        ["dataset_id", "split", "rows", "engines", "rul_min", "rul_max"]
    ]
    compact_quality = quality_summary[
        [
            "dataset_id", "split", "missing_cells", "exact_duplicate_rows",
            "duplicate_engine_cycle_keys", "infinite_numeric_cells",
        ]
    ]
    dropped = feature_audit[feature_audit["decision"] != "retain"][
        ["dataset_id", "feature", "decision", "dominant_value_share"]
    ]
    text = f"""# Preprocessing Summary


## Completed transformations

1. Parsed the 26 whitespace-separated raw columns and assigned explicit names.
2. Verified missing values, infinities, exact duplicates, engine-cycle key duplicates, dtypes, and contiguous cycles.
3. Calculated training RUL as `final_cycle - current_cycle`.
4. Mapped each official test RUL vector entry to its engine and calculated row-level test RUL as `terminal_RUL + last_observed_cycle - current_cycle`.
5. Audited sensor variability on training data only. Exact constants and sensors whose most frequent value covers at least {NEAR_CONSTANT_DOMINANT_SHARE:.0%} of training rows are flagged.
6. Created causal one-cycle deltas and five-cycle rolling means using the current and past observations only.
7. Fit z-score parameters on training data only and reused those parameters for test data.
8. Exported subset-level files plus all-subset merged files with `dataset_id` to prevent unit-ID collisions.

## Dataset output summary

{markdown_table(compact_dataset)}

## Data quality checks

{markdown_table(compact_quality)}

## Flagged sensors by subset

{markdown_table(dropped) if not dropped.empty else 'No sensors were flagged.'}

For a consistent merged schema, the union of subset flags is removed from the merged model-ready files: `{', '.join(global_drop)}`. The unscaled EDA-ready files retain the original measurements for transparency. The decision is reversible and is recorded in `feature_decisions_merged.csv`.

## Simple causal features

Generated columns: `{', '.join(temporal_columns)}`. They use no future cycles. Rolling means include the current cycle and up to four prior cycles; first-cycle deltas are set to zero.

## Leakage controls

- Test statistics never influence fitted scaling parameters.
- RUL and identifiers are never scaled.
- Temporal features never use a future cycle.
- The official test RUL is attached only as an evaluation label. It must not be supplied as an input feature during modelling.
- `observed_last_cycle`, `true_failure_cycle`, `RUL`, `RUL_capped_125`, `rul_at_last_observation`, and `is_last_observation` are label/metadata columns, not predictors.

## Current boundary

Completed: sourcing, provenance, schema, data-quality inspection, RUL labelling, feature flagging, causal starter features, leakage-safe scaling, merging, documentation, and export. Deferred: train/validation strategy, baseline models, hyperparameter tuning, evaluation metrics, error analysis, and deployment. This is intentionally the preprocessing-focused 25–30% milestone.
"""
    (project_root / "reports" / "PREPROCESSING_SUMMARY.md").write_text(text, encoding="utf-8")


def run_pipeline(project_root: Path) -> dict:
    project_root = project_root.resolve()
    raw_dir = project_root / "data" / "raw" / "files"
    processed_dir = project_root / "data" / "processed"
    report_dir = project_root / "reports"
    before_after_dir = report_dir / "before_after"
    before_after_dir.mkdir(parents=True, exist_ok=True)

    expected = ["readme.txt"]
    for dataset_id in DATASET_IDS:
        expected.extend(
            [f"train_{dataset_id}.txt", f"test_{dataset_id}.txt", f"RUL_{dataset_id}.txt"]
        )
    missing = [name for name in expected if not (raw_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing raw files: {missing}")

    quality_records: list[dict] = []
    dataset_records: list[dict] = []
    dtype_records: list[dict] = []
    rul_validation_records: list[dict] = []
    audit_frames: list[pd.DataFrame] = []
    train_labeled: dict[str, pd.DataFrame] = {}
    test_labeled: dict[str, pd.DataFrame] = {}

    for dataset_id in DATASET_IDS:
        train = read_cmapss(raw_dir / f"train_{dataset_id}.txt")
        test = read_cmapss(raw_dir / f"test_{dataset_id}.txt")
        validate_engine_cycles(train, f"train_{dataset_id}.txt")
        validate_engine_cycles(test, f"test_{dataset_id}.txt")
        quality_records.append(audit_quality(train, dataset_id, "train"))
        quality_records.append(audit_quality(test, dataset_id, "test"))
        for split, raw_frame in (("train", train), ("test", test)):
            for column in RAW_COLUMNS:
                dtype_records.append(
                    {
                        "dataset_id": dataset_id,
                        "split": split,
                        "column": column,
                        "dtype": str(raw_frame[column].dtype),
                        "missing_values": int(raw_frame[column].isna().sum()),
                        "unique_values": int(raw_frame[column].nunique(dropna=False)),
                    }
                )

        train = attach_train_rul(train)
        test = attach_test_rul(test, read_official_test_rul(raw_dir / f"RUL_{dataset_id}.txt"))
        train.insert(0, "dataset_id", dataset_id)
        test.insert(0, "dataset_id", dataset_id)

        if not (train.loc[train["is_last_observation"] == 1, "RUL"] == 0).all():
            raise AssertionError(f"{dataset_id}: terminal training RUL must be zero")
        test_last = test.loc[test["is_last_observation"] == 1]
        if not (test_last["RUL"] == test_last["rul_at_last_observation"]).all():
            raise AssertionError(f"{dataset_id}: official test RUL mapping failed")
        if (train["RUL"] < 0).any() or (test["RUL"] < 0).any():
            raise AssertionError(f"{dataset_id}: negative RUL generated")
        rul_validation_records.extend(
            [
                {
                    "dataset_id": dataset_id,
                    "check": "training_terminal_rul_is_zero",
                    "expected_engine_rows": int(train["unit_id"].nunique()),
                    "observed_engine_rows": int((train["is_last_observation"] == 1).sum()),
                    "passed": bool(
                        (train.loc[train["is_last_observation"] == 1, "RUL"] == 0).all()
                    ),
                },
                {
                    "dataset_id": dataset_id,
                    "check": "test_terminal_rul_matches_official_vector",
                    "expected_engine_rows": int(len(read_official_test_rul(raw_dir / f"RUL_{dataset_id}.txt"))),
                    "observed_engine_rows": int((test["is_last_observation"] == 1).sum()),
                    "passed": bool(
                        (test_last["RUL"] == test_last["rul_at_last_observation"]).all()
                    ),
                },
            ]
        )

        train_labeled[dataset_id] = train
        test_labeled[dataset_id] = test
        audit_frames.append(audit_sensors(train, dataset_id))
        for split, frame in (("train", train), ("test", test)):
            dataset_records.append(
                {
                    "dataset_id": dataset_id,
                    "split": split,
                    "rows": int(len(frame)),
                    "engines": int(frame["unit_id"].nunique()),
                    "observed_cycle_min": int(frame["cycle"].min()),
                    "observed_cycle_max": int(frame["cycle"].max()),
                    "rul_min": int(frame["RUL"].min()),
                    "rul_max": int(frame["RUL"].max()),
                    "last_observation_rul_min": int(
                        frame.loc[frame["is_last_observation"] == 1, "RUL"].min()
                    ),
                    "last_observation_rul_max": int(
                        frame.loc[frame["is_last_observation"] == 1, "RUL"].max()
                    ),
                }
            )

    quality_summary = pd.DataFrame(quality_records)
    dataset_summary = pd.DataFrame(dataset_records)
    feature_audit = pd.concat(audit_frames, ignore_index=True)
    subset_drop = {
        dataset_id: feature_audit.loc[
            (feature_audit["dataset_id"] == dataset_id)
            & (feature_audit["decision"] != "retain"),
            "feature",
        ].tolist()
        for dataset_id in DATASET_IDS
    }
    global_drop = sorted(
        set().union(*[set(values) for values in subset_drop.values()]),
        key=lambda name: int(name.split("_")[1]),
    )

    subset_scalers = []
    comparison_rows = []
    all_temporal_columns: list[str] = []
    for dataset_id in DATASET_IDS:
        retained = [column for column in SENSOR_COLUMNS if column not in subset_drop[dataset_id]]
        train, temporal_columns = add_causal_temporal_features(train_labeled[dataset_id], retained)
        test, test_temporal = add_causal_temporal_features(test_labeled[dataset_id], retained)
        assert temporal_columns == test_temporal
        all_temporal_columns = temporal_columns
        scale_columns = SETTING_COLUMNS + retained + temporal_columns
        params = fit_standardizer(train, scale_columns)
        params.insert(0, "dataset_id", dataset_id)
        subset_scalers.append(params)
        train_scaled = apply_standardizer(train, params, scale_columns)
        test_scaled = apply_standardizer(test, params, scale_columns)

        subset_folder = processed_dir / "by_subset" / dataset_id
        save_csv(train_scaled[model_ready_columns(scale_columns, "train")], subset_folder / f"{dataset_id}_train_model_ready.csv")
        save_csv(test_scaled[model_ready_columns(scale_columns, "test")], subset_folder / f"{dataset_id}_test_model_ready.csv")
        save_csv(params, subset_folder / f"{dataset_id}_train_fitted_scaler.csv")
        save_csv(train, processed_dir / "eda_ready" / f"{dataset_id}_train_eda_ready_unscaled.csv")
        save_csv(test, processed_dir / "eda_ready" / f"{dataset_id}_test_eda_ready_unscaled.csv")

        raw_lines = (raw_dir / f"train_{dataset_id}.txt").read_text(encoding="utf-8", errors="replace").splitlines()[:5]
        (before_after_dir / f"{dataset_id}_raw_source_first5.txt").write_text("\n".join(raw_lines) + "\n", encoding="utf-8")
        save_csv(train.head(8), before_after_dir / f"{dataset_id}_parsed_before_first8.csv")
        save_csv(train_scaled[model_ready_columns(scale_columns, "train")].head(8), before_after_dir / f"{dataset_id}_processed_after_first8.csv")

        for row_index in train.head(3).index:
            for feature in SETTING_COLUMNS + SENSOR_COLUMNS:
                decision = "retained"
                processed_value = np.nan
                if feature in subset_drop[dataset_id]:
                    decision = "flagged_and_removed_from_subset_model_ready"
                else:
                    processed_value = float(train_scaled.loc[row_index, feature])
                comparison_rows.append(
                    {
                        "dataset_id": dataset_id,
                        "unit_id": int(train.loc[row_index, "unit_id"]),
                        "cycle": int(train.loc[row_index, "cycle"]),
                        "feature": feature,
                        "original_value": float(train.loc[row_index, feature]),
                        "processed_value": processed_value,
                        "decision": decision,
                    }
                )

    save_csv(pd.concat(subset_scalers, ignore_index=True), report_dir / "scaling_parameters_by_subset.csv")
    save_csv(pd.DataFrame(comparison_rows), before_after_dir / "before_after_comparison_long.csv")

    merged_train = pd.concat(train_labeled.values(), ignore_index=True)
    merged_test = pd.concat(test_labeled.values(), ignore_index=True)
    merged_retained = [column for column in SENSOR_COLUMNS if column not in global_drop]
    merged_train, merged_temporal = add_causal_temporal_features(merged_train, merged_retained)
    merged_test, merged_test_temporal = add_causal_temporal_features(merged_test, merged_retained)
    assert merged_temporal == merged_test_temporal
    merged_scale_columns = SETTING_COLUMNS + merged_retained + merged_temporal
    merged_params = fit_standardizer(merged_train, merged_scale_columns)
    merged_params.insert(0, "dataset_id", "ALL_TRAIN_SUBSETS")
    merged_train_scaled = apply_standardizer(merged_train, merged_params, merged_scale_columns)
    merged_test_scaled = apply_standardizer(merged_test, merged_params, merged_scale_columns)

    save_csv(
        merged_train_scaled[model_ready_columns(merged_scale_columns, "train")],
        processed_dir / "merged" / "train_all_subsets_model_ready.csv",
    )
    save_csv(
        merged_test_scaled[model_ready_columns(merged_scale_columns, "test")],
        processed_dir / "merged" / "test_all_subsets_model_ready.csv",
    )
    save_csv(merged_params, processed_dir / "merged" / "all_subsets_train_fitted_scaler.csv")
    save_csv(merged_train, processed_dir / "merged" / "train_all_subsets_eda_ready_unscaled.csv")
    save_csv(merged_test, processed_dir / "merged" / "test_all_subsets_eda_ready_unscaled.csv")

    decisions = []
    for sensor in SENSOR_COLUMNS:
        flagged_in = [key for key, values in subset_drop.items() if sensor in values]
        decisions.append(
            {
                "feature": sensor,
                "merged_decision": "drop" if sensor in global_drop else "retain",
                "flagged_in_subsets": ",".join(flagged_in),
                "reason": (
                    "union rule: flagged in at least one training subset"
                    if sensor in global_drop
                    else "not flagged in any training subset"
                ),
            }
        )
    save_csv(pd.DataFrame(decisions), report_dir / "feature_decisions_merged.csv")
    save_csv(feature_audit, report_dir / "feature_quality_by_subset.csv")
    save_csv(quality_summary, report_dir / "data_quality_summary.csv")
    save_csv(dataset_summary, report_dir / "dataset_summary.csv")
    save_csv(pd.DataFrame(dtype_records), report_dir / "schema_and_dtype_summary.csv")
    save_csv(pd.DataFrame(rul_validation_records), report_dir / "rul_validation_summary.csv")

    checksum_paths = sorted(
        list((project_root / "data" / "raw").rglob("*"))
        + [project_root / "docs" / "Damage_Propagation_Modeling_2008.pdf"]
    )
    checksum_paths = [path for path in checksum_paths if path.is_file()]
    checksum_text = "\n".join(
        f"{sha256(path)}  {path.relative_to(project_root)}" for path in checksum_paths
    ) + "\n"
    (report_dir / "checksums_sha256.txt").write_text(checksum_text, encoding="utf-8")

    write_preprocessing_summary(
        project_root,
        dataset_summary,
        quality_summary,
        feature_audit,
        global_drop,
        merged_temporal,
    )

    manifest = {
        "project": "Predictive Remaining Useful Life (RUL) Estimation of Aircraft Turbofan Engines",
        "milestone": "25-30% preprocessing-focused",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "datasets": list(DATASET_IDS),
        "raw_schema_columns": RAW_COLUMNS,
        "rul_cap_cycles": RUL_CAP,
        "near_constant_dominant_share_threshold": NEAR_CONSTANT_DOMINANT_SHARE,
        "merged_dropped_sensors": global_drop,
        "merged_retained_sensors": merged_retained,
        "causal_temporal_features": merged_temporal,
        "scaler": "z-score, population standard deviation, fit on training rows only",
        "counts": dataset_records,
    }
    (report_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
