# Predictive Remaining Useful Life (RUL) Estimation of Aircraft Turbofan Engines

## Project milestone report: 25–30% completion

### 1. Problem Statement

Unexpected degradation in aircraft propulsion systems can create safety, availability, and maintenance-cost concerns. A prognostics system attempts to estimate how much useful operation remains before a defined failure threshold is reached. In this project, Remaining Useful Life (RUL) is expressed in operating cycles.

The machine-learning problem is to learn a mapping from a multivariate sequence of operating settings and sensor measurements to the number of cycles remaining before simulated engine failure. Each engine is observed repeatedly over time. Training trajectories end at failure, whereas test trajectories are truncated before failure. The practical challenge is therefore not ordinary independent-row regression: observations from one engine are temporally related, engines have different initial wear, operating conditions influence sensor levels, and preprocessing must not use future or test information.

This milestone establishes a trustworthy data foundation before model development. It obtains all four C-MAPSS subsets, preserves the source, validates structure and quality, creates correct RUL labels, documents low-information sensors, applies train-fitted scaling, engineers a small number of causal time-series features, and creates subset-level and merged files.

### 2. Literature Review

Saxena, Goebel, Simon, and Eklund (2008) introduced the run-to-failure simulation approach behind this benchmark. C-MAPSS represents a large commercial turbofan through a thermodynamic simulation. Degradation is injected through changes in component flow and efficiency, and trajectories continue until a failure criterion is reached. This work is foundational because it explains why the outputs resemble engine sensor time series while still being synthetic rather than airline operational records.

Heimes (2008) addressed the PHM 2008 RUL challenge with recurrent neural networks. The work demonstrated that sequence models can exploit temporal dependencies rather than treating cycles as unrelated observations. It also helped popularize piecewise-linear RUL targets, where very large early-life RUL values are capped. The current package therefore preserves uncapped RUL as ground truth and provides `RUL_capped_125` only as an optional modelling target.

Ramasso and Saxena (2014) examined benchmarking across the C-MAPSS datasets and highlighted that comparisons depend on consistent datasets, preprocessing, validation, and metrics. Their analysis supports treating FD001–FD004 as distinct experimental conditions rather than assuming that performance on the simplest subset generalizes automatically.

Zheng et al. (2017) applied Long Short-Term Memory networks to RUL estimation, emphasizing the value of sequence information and long-term dependencies. Li, Ding, and Sun (2018) instead used deep convolutional networks with time windows, allowing learned feature extraction directly from normalized sensor sequences. Together these studies motivate future comparison between an interpretable tabular baseline and sequence-based models. They also reinforce why scaling, temporal window construction, and engine-wise splitting must be designed carefully.

Arias Chao, Kulkarni, Goebel, and Fink (2021) later presented N-CMAPSS, which has higher-fidelity run-to-failure trajectories and uses real flight-condition inputs with simulated engine degradation. That dataset is related but not interchangeable with the classic 2008 C-MAPSS files used here. The distinction is important: this project uses classic FD001–FD004, not N-CMAPSS, and it does not claim to use real airline engine-failure histories.

The literature suggests three practical conclusions for this milestone. First, correct sequence and label construction is as important as model choice. Second, operational conditions and fault-mode complexity differ substantially across subsets. Third, test leakage can make results look unrealistically good; scaling, feature selection, temporal features, and validation must be learned from or restricted to training history.

### 3. Scope

#### In scope for the 25–30% milestone

- NASA C-MAPSS FD001, FD002, FD003, and FD004.
- Source provenance, raw archive preservation, extraction, and checksums.
- Parsing the whitespace-separated data and assigning the 26-column schema.
- Data-quality inspection: missing values, infinities, duplicates, duplicate engine-cycle keys, dtypes, cycle order, and engine counts.
- Training and test RUL label construction.
- Exact/near-constant sensor auditing based only on training data.
- Leakage-safe standardization.
- A small, transparent set of causal delta and rolling-mean features.
- Per-subset and cross-subset merging with `dataset_id`.
- EDA-ready and model-ready CSV outputs.
- Documentation, before/after evidence, tests, and a runnable script/notebook.

#### Out of scope until later phases

- Selecting a final ML or deep-learning architecture.
- Hyperparameter tuning or final feature selection.
- Formal train/validation/test experiments.
- RMSE, MAE, NASA asymmetric score, uncertainty, or confidence intervals.
- Deployment, live monitoring, and integration with a maintenance system.
- Safety certification or conclusions about real aircraft airworthiness.

### 4. Objectives

#### Primary objective

Develop a reproducible and leakage-aware preprocessing foundation for later supervised estimation of turbofan-engine RUL in cycles.

#### Specific objectives

1. Preserve and verify the complete official C-MAPSS source material.
2. Convert all raw trajectories into named, typed tabular data without altering raw files.
3. Verify that every engine-cycle observation is structurally valid.
4. Derive training RUL and attach official test RUL correctly.
5. Quantify and document sensor quality instead of removing columns without evidence.
6. Fit transformations on training data only and reuse them on test data.
7. Add only causal time-series features that are explainable at the current milestone.
8. Create consistent, merge-safe outputs for EDA and later modelling.
9. Make every transformation inspectable through code, samples, summaries, and tests.

### 5. Dataset Description

The classic C-MAPSS package contains multiple multivariate time series. A trajectory represents one simulated engine. Every row is one operational cycle and has 26 fields: unit number, cycle, three operational settings, and 21 sensor measurements. Sensor noise is included. Engines begin in a nominal state with unobserved initial wear/manufacturing variation and later develop a simulated fault. Training trajectories run to the defined failure point; test trajectories stop earlier, with a separate RUL vector stating how many additional cycles remain after each engine's final observed test row.

| Subset | Training engines | Test engines in files | Operating conditions | Fault modes |
| --- | ---: | ---: | --- | --- |
| FD001 | 100 | 100 | 1 (sea level) | 1: HPC degradation |
| FD002 | 260 | 259 | 6 | 1: HPC degradation |
| FD003 | 100 | 100 | 1 (sea level) | 2: HPC and fan degradation |
| FD004 | 249 | 248 | 6 | 2: HPC and fan degradation |

The included 2008 README states 248 FD004 training trajectories and 249 test trajectories, but the supplied files contain 249 unique training engines and 248 paired test engines/RUL labels. The pipeline validates against the actual files and records those observed counts. This apparent transposition in the source README is documented rather than silently copied.

The setting and sensor columns are anonymized. Their correct safe descriptions are operational setting 1–3 and sensor measurement 1–21; inventing physical units or engine-variable names would not be supported by the distributed data dictionary.

### 6. Methodology and Current Progress

#### 6.1 Acquisition and preservation

The NASA PCoE archive is stored as `data/raw/source_archive/CMAPSSData.zip`. Extracted source TXT files and the original README are in `data/raw/files/`. They are never overwritten. SHA-256 checksums provide evidence that rerunning preprocessing does not mutate the source.

#### 6.2 Parsing and schema

The code reads arbitrary whitespace, checks for exactly 26 columns, assigns explicit names, stores identifiers/cycles as integers, and stores settings/sensors as floating-point measurements. `dataset_id` is added only to derived data so that unit 1 in FD001 cannot be confused with unit 1 in another subset.

#### 6.3 Data-quality validation

For every train/test file, the pipeline counts missing and infinite values, exact duplicate rows, and duplicate `(unit_id, cycle)` keys. It also verifies that cycles for each engine are ordered and contiguous from 1. Actual results are generated in `reports/data_quality_summary.csv` rather than being hard-coded in this report.

#### 6.4 RUL construction

For training engine *i* at cycle *t*:

`RUL(i,t) = max_training_cycle(i) - t`

Thus the final training observation has RUL 0.

For test engine *i*, NASA supplies `RUL_terminal(i)`, the number of cycles remaining after its last observed cycle. Therefore:

`RUL(i,t) = RUL_terminal(i) + last_observed_cycle(i) - t`

The pipeline asserts that every final test row exactly matches the corresponding official RUL-vector value. It also exports an optional `RUL_capped_125 = min(RUL, 125)` label. Labels and failure-derived metadata are clearly separated from predictor columns.

#### 6.5 Constant and near-constant sensor policy

Sensor decisions are computed separately from each training subset. A sensor is exact-constant when it has one unique training value. A nonconstant sensor is called near-constant when its most common training value occupies at least 95% of rows. The rule is simple, auditable, and does not use the test distribution.

Subset model-ready files remove their locally flagged sensors. For a single consistent all-subset schema, the merged files use the union of subset flags. Unscaled EDA-ready files retain every original sensor so the removal is transparent and reversible. This is an initial quality rule, not a claim that all flagged sensors are universally useless; later validation may compare alternative feature policies.

#### 6.6 Temporal features

For eight commonly analysed sensor channels, the project generates a one-cycle difference and a five-cycle rolling mean. Both are causal: they use the current and previous cycles only. A first-cycle difference has no predecessor and is set to zero. These features are starter examples for later window-based modelling, not an exhaustive feature-engineering stage.

#### 6.7 Scaling without leakage

Z-score mean and population standard deviation are fitted only on training rows. Exactly the same fitted values transform the corresponding test data. Identifiers, cycle, RUL labels, terminal RUL, failure-cycle metadata, and last-observation flags are not scaled and must not be model predictors. A zero-variance guard uses scale 1.0 and is explicitly recorded.

#### 6.8 Delivered outputs

- `data/processed/by_subset/`: model-ready train/test and fitted scaler for each FD subset.
- `data/processed/eda_ready/`: labelled, unscaled, full-sensor subset files.
- `data/processed/merged/`: FD001–FD004 merged train/test files, scaler, and unscaled EDA versions.
- `reports/`: dataset counts, quality results, feature audit/decisions, scaler parameters, checksums, run manifest, and before/after examples.
- `notebooks/`: a concise walkthrough suitable for demonstration.
- `tests/`: automated checks for the most important RUL and scaling rules.

### 7. Planned Next Phase

The next phase should create engine-wise training and validation splits so cycles from the same engine never occur in both sets. It should establish simple baselines (last-value or mean prediction, linear/ridge regression, random forest or gradient boosting), define MAE/RMSE and the NASA asymmetric scoring function, and compare uncapped versus capped labels. Only after baselines and leakage checks should sequence windows and LSTM/CNN models be introduced. FD001 is the recommended starting subset; FD002–FD004 test robustness to more operating conditions and fault modes.

### 8. Limitations and Ethical Interpretation

The dataset is a benchmark generated by simulation. Results cannot directly establish maintenance intervals, failure probability, or airworthiness for a real engine. Sensor names and physical units are not disclosed in the distributed files, failure criteria are simulation-specific, and fleet/manufacturing variation is simplified. Any later predictive result should therefore be presented as benchmark performance on simulated trajectories, not as a deployable aviation safety system.

### 9. References (APA-style)

Arias Chao, M., Kulkarni, C., Goebel, K., & Fink, O. (2021). Aircraft engine run-to-failure dataset under real flight conditions for prognostics and diagnostics. *Data, 6*(1), 5. <https://doi.org/10.3390/data6010005>

Heimes, F. O. (2008). Recurrent neural networks for remaining useful life estimation. In *2008 International Conference on Prognostics and Health Management* (pp. 1–6). IEEE. <https://doi.org/10.1109/PHM.2008.4711422>

Li, X., Ding, Q., & Sun, J.-Q. (2018). Remaining useful life estimation in prognostics using deep convolution neural networks. *Reliability Engineering & System Safety, 172*, 1–11. <https://doi.org/10.1016/j.ress.2017.11.021>

NASA. (n.d.). *CMAPSS jet engine simulated data*. NASA Open Data Portal. Retrieved September 2, 2026, from <https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data>

NASA Ames Prognostics Center of Excellence. (2008). *Turbofan engine degradation simulation data set* [Data set]. NASA Prognostics Data Repository. <https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/>

Prognostics and Health Management Society. (n.d.). *NASA Prognostics Center of Excellence data set repository mirror*. Retrieved September 2, 2026, from <https://data.phmsociety.org/nasa/>

Ramasso, E., & Saxena, A. (2014). Performance benchmarking and analysis of prognostic methods for CMAPSS datasets. *International Journal of Prognostics and Health Management, 5*(2). <https://doi.org/10.36001/ijphm.2014.v5i2.2236>

Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). Damage propagation modeling for aircraft engine run-to-failure simulation. In *2008 International Conference on Prognostics and Health Management* (pp. 1–9). IEEE. <https://doi.org/10.1109/PHM.2008.4711414>

Zheng, S., Ristovski, K., Farahat, A., & Gupta, C. (2017). Long short-term memory network for remaining useful life estimation. In *2017 IEEE International Conference on Prognostics and Health Management* (pp. 88–95). IEEE. <https://doi.org/10.1109/ICPHM.2017.7998311>
