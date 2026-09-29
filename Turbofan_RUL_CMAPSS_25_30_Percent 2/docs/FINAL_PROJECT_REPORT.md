# Predictive Remaining Useful Life Estimation of Aircraft Turbofan Engines

> Baseline-results report. Model choices are mapped to the supplied Machine Learning topics in `SYLLABUS_MODEL_SCOPE.md`.

## Abstract

This project estimates the remaining useful life (RUL) of simulated turbofan engines using classical machine learning. It uses the NASA C-MAPSS FD001–FD004 benchmark. The project preserves the original files, checks their structure, derives cycle-level RUL, explores the data, creates causal sensor features, and compares four regressors. Engines rather than rows are separated for validation. Model choice uses a partial-history endpoint from each held-out training engine. The chosen model is refitted on all training engines and evaluated once against the official RUL value at the final observed cycle of each test engine. Official-test RMSE ranges from 27.66 to 38.50 cycles across the four subsets. Results are reproducible but a single validation split is unstable, and benchmark performance is not evidence of safety for real aircraft maintenance.

## Problem and objective

Maintenance planners would benefit from estimates of how many cycles an engine can continue to operate before a defined failure threshold. The objective here is to predict that remaining cycle count from operational settings and sensor history. The task is supervised regression. The dataset is simulated; it is an academic prognostics benchmark, not operational flight data.

## Dataset and provenance

The source is NASA's C-MAPSS turbofan engine degradation simulation data, preserved in `data/raw/source_archive/CMAPSSData.zip` and as untouched text files in `data/raw/files/`. The source archive, paper, checksums, and retrieval explanation are recorded in `docs/SOURCE_PROVENANCE.md` and `reports/checksums_sha256.txt`. Each training or test row has 26 values: unit ID, cycle, three operational settings, and 21 sensors. FD001–FD004 vary in number of operating conditions and fault modes. Each subset has `train_FD00X.txt`, `test_FD00X.txt`, and `RUL_FD00X.txt`; the last is a vector of true RUL values at the test engines' final observed cycles.

| Subset | Train engines | Test engines | Operating conditions | Fault modes |
| --- | ---: | ---: | ---: | ---: |
| FD001 | 100 | 100 | 1 | 1 |
| FD002 | 260 | 259 | 6 | 1 |
| FD003 | 100 | 100 | 1 | 2 |
| FD004 | 249 | 248 | 6 | 2 |

These FD001–FD004 files differ from the original PHM08 challenge package named `train.txt`, `test.txt`, and `final_test.txt`. The code and all results in this repository use FD001–FD004.

## Preprocessing and exploratory analysis

The preprocessing pipeline assigns column names and checks missing values, infinite values, exact duplicates, duplicate engine-cycle keys, numeric types, and contiguous cycles. The preserved quality report records zero missing cells, infinite cells, and duplicate keys in all eight train/test files. Training RUL is the final recorded cycle of an engine minus its current cycle. The official test RUL vector is mapped by engine and used as an evaluation label. `RUL_capped_125` is exported as an optional alternative; the models in this report use uncapped `RUL`.

Training-only sensor-variation rules flag channels that are constant or whose most common value occupies at least 95% of rows. One-cycle differences and five-cycle rolling means use only current and prior observations. The earlier processed exports use training-fitted z-score parameters. For the modeling experiment, raw files are reloaded and sensor selection is fitted **after** the engine-wise split, so validation engines do not influence it. Ridge scaling is fitted inside its training pipeline. The EDA in `reports/eda/` shows unequal engine lifetimes and example sensor trajectories; these examples illustrate degradation patterns without claiming that one sensor alone proves engine health.

## Experimental design

Within each subset, a fixed-seed group split reserves 20% of training engines for validation. One endpoint between 50% and 85% of each held-out engine's full history is chosen to mimic a truncated test history. Predictions are compared with the known RUL at those endpoints. The candidates are a median baseline, Ridge regression, Random Forest, and Histogram Gradient Boosting. Validation RMSE selects one model. That model is refitted on all training engines, then predicts one RUL for each official test engine at its last observed cycle. Official test RUL values are excluded from feature selection, model fitting, and model choice.

Inputs are cycle, three operational settings, retained sensors, and the causal difference/rolling features. Unit ID is used only for grouping. The label, true failure cycle, last-observation metadata, and official RUL vector are never predictors. The exact validation engine IDs, selected sensors, and winner for every subset are in each `reports/modeling/FD00X/protocol.json`.

## Results

MAE and RMSE are in cycles. Lower is better. R² can be negative when a model is worse than the mean predictor on that validation sample. The PHM asymmetric score is preserved in the CSV files; it cannot be compared directly across subsets with different engine counts.

| Subset | Validation winner | Validation RMSE | Validation R² | Official test MAE | Official test RMSE | Official test R² |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| FD001 | Random Forest | 27.17 | −0.72 | 21.21 | 28.68 | 0.52 |
| FD002 | Histogram Gradient Boosting | 32.16 | −0.60 | 20.27 | 27.66 | 0.74 |
| FD003 | Histogram Gradient Boosting | 24.87 | 0.68 | 23.89 | 34.81 | 0.29 |
| FD004 | Histogram Gradient Boosting | 45.19 | −0.72 | 27.72 | 38.50 | 0.50 |

The full-precision values and one row per test engine are in `reports/modeling/`. The FD004 error is highest, consistent with a harder subset containing multiple operating conditions and fault modes, though the experiment alone does not establish causation. FD003's official-test result is weaker than its validation result, another sign that one validation split can mislead.

## Error analysis

The model overestimated life for 65 of 100 FD001 engines, 150 of 259 FD002 engines, 76 of 100 FD003 engines, and 175 of 248 FD004 engines. An overestimate means the predicted remaining cycles exceed the actual remaining cycles; that is the more dangerous error for a maintenance-use interpretation. The models were generally more accurate at actual RUL below 25 cycles than at longer remaining lives, but individual large errors remain. The RUL-band table, error-direction counts, twenty largest errors, and plot are in `reports/modeling/`.

## Limitations and next research improvements

The data are simulated and cover restricted fault and operating scenarios. Initial wear and degradation onset are not directly observed, and sensor noise complicates interpretation. The current protocol uses one engine-wise validation split and one partial-history endpoint per validation engine. Three validation R² values are negative. Hyperparameters and training-row weighting were not optimized; long-lived engines contribute more training rows. These choices make the results credible as reproducible **classical baselines**, but not as a deployable aircraft safety system. A strong follow-up study would use repeated group cross-validation, multiple truncation points per validation engine, calibrated uncertainty intervals, and a model-selection objective that accounts for late-prediction cost. Any such search must leave the official test labels untouched until final evaluation.

## Reproduction

From the project directory, use Python and `requirements.txt`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 run_pipeline.py
python3 run_eda.py
python3 train_models.py
python3 run_error_analysis.py
python3 -m unittest discover -s tests -v
```

The pipeline exports preprocessed data and reports. The EDA script exports figures and tables. The modeling script writes validation and official-test metrics, engine-level predictions, plots, and protocol files. The error-analysis script summarizes prediction errors. The nine automated tests passed for this baseline prototype on 29 September 2026. Re-running `run_pipeline.py` may refresh generated files and timestamps; inspect Git changes before committing regenerated artifacts.

## References

1. Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). *Damage propagation modeling for aircraft engine run-to-failure simulation*. 2008 International Conference on Prognostics and Health Management. <https://doi.org/10.1109/PHM.2008.4711414>
2. Ramasso, E., & Saxena, A. (2014). *Performance benchmarking and analysis of prognostic methods for C-MAPSS datasets*. International Journal of Prognostics and Health Management. <https://doi.org/10.36001/ijphm.2014.v5i2.2236>
3. Wang, T., Yu, J., Siegel, D., & Lee, J. (2008). *A similarity-based prognostics approach for Remaining Useful Life estimation of engineered systems*. 2008 International Conference on Prognostics and Health Management. <https://doi.org/10.1109/PHM.2008.4711421>
