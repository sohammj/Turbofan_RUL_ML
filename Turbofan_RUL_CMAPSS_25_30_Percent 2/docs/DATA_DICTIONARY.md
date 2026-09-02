# Data Dictionary

## Raw schema

Every raw train/test row has 26 whitespace-separated numeric fields.

| Position | Derived name | Type | Meaning | Unit/status |
| ---: | --- | --- | --- | --- |
| 1 | `unit_id` | integer | Simulated engine trajectory identifier within a subset | Identifier; restarts in each FD subset |
| 2 | `cycle` | integer | Sequential operational cycle for that engine | Cycles |
| 3–5 | `op_setting_1` … `op_setting_3` | float | Operating-condition settings affecting engine performance | Units not disclosed |
| 6–26 | `sensor_1` … `sensor_21` | float | Noisy simulated sensor measurements | Names/units not disclosed |

The source README's phrase “sensor measurement 26” is best read as “column 26”; because columns 1–5 are ID/cycle/settings, columns 6–26 contain 21 sensor channels.

## Added metadata and labels

| Column | Type | Meaning | Predictor? |
| --- | --- | --- | --- |
| `dataset_id` | string | FD001, FD002, FD003, or FD004 | Categorical context if the experimental design allows it |
| `observed_last_cycle` | integer | Last cycle visible in the supplied trajectory | No; sequence/label metadata |
| `true_failure_cycle` | integer | Training final cycle, or test last observed cycle plus official terminal RUL | No; target-derived metadata |
| `RUL` | integer | Remaining cycles until the defined simulated failure point | Target only |
| `RUL_capped_125` | integer | Optional piecewise target `min(RUL, 125)` | Target only |
| `rul_at_last_observation` | integer | Official NASA test RUL for the engine's final observed row; test exports only | No; evaluation ground truth |
| `is_last_observation` | integer flag | 1 for the final supplied row of an engine, otherwise 0 | No; evaluation/selection metadata |

## Causal starter features

For sensors 2, 3, 4, 7, 11, 12, 15, and 21 when retained:

| Pattern | Meaning |
| --- | --- |
| `sensor_N_delta_1` | Current measurement minus the previous cycle's measurement for the same engine; 0 at its first cycle |
| `sensor_N_rolling_mean_5` | Mean of the current and up to four preceding cycles for the same engine |

The model-ready versions of setting, sensor, and temporal-feature columns are z-scores fitted from training rows. Identifiers and target/metadata columns remain unscaled.

