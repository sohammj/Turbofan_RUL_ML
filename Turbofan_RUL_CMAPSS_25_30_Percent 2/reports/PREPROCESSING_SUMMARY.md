# Preprocessing Summary

## Completed transformations

The pipeline names the 26 raw fields, validates engine-cycle sequences and data quality, derives training RUL, maps the official test RUL labels, flags low-variation sensors from training data, creates causal temporal features, fits scaling parameters on training data, and exports subset and merged tables.

## Dataset output summary

| dataset_id | split | rows | engines | rul_min | rul_max |
| --- | --- | --- | --- | --- | --- |
| FD001 | train | 20631 | 100 | 0 | 361 |
| FD001 | test | 13096 | 100 | 7 | 340 |
| FD002 | train | 53759 | 260 | 0 | 377 |
| FD002 | test | 33991 | 259 | 6 | 377 |
| FD003 | train | 24720 | 100 | 0 | 524 |
| FD003 | test | 16596 | 100 | 6 | 483 |
| FD004 | train | 61249 | 249 | 0 | 542 |
| FD004 | test | 41214 | 248 | 6 | 553 |

## Data quality checks

| dataset_id | split | missing_cells | exact_duplicate_rows | duplicate_engine_cycle_keys | infinite_numeric_cells |
| --- | --- | --- | --- | --- | --- |
| FD001 | train | 0 | 0 | 0 | 0 |
| FD001 | test | 0 | 0 | 0 | 0 |
| FD002 | train | 0 | 0 | 0 | 0 |
| FD002 | test | 0 | 0 | 0 | 0 |
| FD003 | train | 0 | 0 | 0 | 0 |
| FD003 | test | 0 | 0 | 0 | 0 |
| FD004 | train | 0 | 0 | 0 | 0 |
| FD004 | test | 0 | 0 | 0 | 0 |

## Flagged sensors by subset

| dataset_id | feature | decision | dominant_value_share |
| --- | --- | --- | --- |
| FD001 | sensor_1 | drop_exact_constant | 1.0 |
| FD001 | sensor_5 | drop_exact_constant | 1.0 |
| FD001 | sensor_6 | drop_near_constant | 0.9803208763511221 |
| FD001 | sensor_10 | drop_exact_constant | 1.0 |
| FD001 | sensor_16 | drop_exact_constant | 1.0 |
| FD001 | sensor_18 | drop_exact_constant | 1.0 |
| FD001 | sensor_19 | drop_exact_constant | 1.0 |
| FD003 | sensor_1 | drop_exact_constant | 1.0 |
| FD003 | sensor_5 | drop_exact_constant | 1.0 |
| FD003 | sensor_16 | drop_exact_constant | 1.0 |
| FD003 | sensor_18 | drop_exact_constant | 1.0 |
| FD003 | sensor_19 | drop_exact_constant | 1.0 |

For a consistent merged schema, the union of subset flags is removed from the merged model-ready files: `sensor_1, sensor_5, sensor_6, sensor_10, sensor_16, sensor_18, sensor_19`. The unscaled EDA-ready files retain the original measurements for transparency. The decision is reversible and is recorded in `feature_decisions_merged.csv`.

## Simple causal features

Generated columns: `sensor_2_delta_1, sensor_2_rolling_mean_5, sensor_3_delta_1, sensor_3_rolling_mean_5, sensor_4_delta_1, sensor_4_rolling_mean_5, sensor_7_delta_1, sensor_7_rolling_mean_5, sensor_11_delta_1, sensor_11_rolling_mean_5, sensor_12_delta_1, sensor_12_rolling_mean_5, sensor_15_delta_1, sensor_15_rolling_mean_5, sensor_21_delta_1, sensor_21_rolling_mean_5`. They use no future cycles. Rolling means include the current cycle and up to four prior cycles; first-cycle deltas are set to zero.

## Leakage controls

- Test statistics never influence fitted scaling parameters.
- RUL and identifiers are never scaled.
- Temporal features never use a future cycle.
- The official test RUL is attached only as an evaluation label. It must not be supplied as an input feature during modelling.
- `observed_last_cycle`, `true_failure_cycle`, `RUL`, `RUL_capped_125`, `rul_at_last_observation`, and `is_last_observation` are label/metadata columns, not predictors.

## Downstream work

This report covers the preprocessing stage. Model training, official-test evaluation, error analysis, and repeated engine-wise validation are documented in `docs/FINAL_PROJECT_REPORT.md`, `reports/modeling/`, and `reports/robustness/`. This academic benchmark has not been deployed for maintenance decisions.
