# Technical explainer: NASA C-MAPSS turbofan RUL project

> Companion to the final report. All numerical findings below are from this repository's saved outputs; the data are simulated and must not be presented as real aircraft maintenance performance.

## 1. What is being predicted?

Remaining useful life (RUL) is the number of operating cycles left until the simulated failure threshold. This is a supervised regression problem: the target is a number, not a class label. For each training engine and cycle, `RUL = last training cycle for that engine − current cycle`. A training trajectory ends at failure, so its last row has RUL zero. A test trajectory ends earlier; NASA supplies one true RUL value per test engine at its last observed cycle. The model predicts that value from the available history. The official test answer is never a predictor.

## 2. Which dataset and files?

The experiments use NASA's C-MAPSS turbofan degradation simulation FD001–FD004, not the differently named original PHM08 challenge package `train.txt`, `test.txt`, `final_test.txt`. The untouched source archive and extracted TXT files are in `data/raw/`; provenance and SHA-256 hashes are in `docs/SOURCE_PROVENANCE.md` and `reports/checksums_sha256.txt`. Each subset has `train_FD00X.txt`, `test_FD00X.txt`, `RUL_FD00X.txt`, and a README. FD001 has 100 training and 100 test engines; FD002 260 and 259; FD003 100 and 100; FD004 249 and 248. FD001/FD003 have one operating condition; FD002/FD004 have six. FD001/FD002 have one fault mode; FD003/FD004 have two.

Each raw row represents one engine at one cycle and contains exactly 26 numeric fields: engine ID, cycle number, three operational settings, and 21 sensor readings. The engine ID identifies a trajectory; it is not an explanatory predictor. The exact sensor names/units supplied with the data are in `docs/DATA_DICTIONARY.md`. Some channels are nearly constant in a subset and contribute little variation. The labels in `RUL_FD00X.txt` are a separate vector, not a twenty-seventh raw sensor column.

## 3. What did preprocessing do?

`run_pipeline.py` reads the source TXT files, assigns column names, checks numeric types, missing/infinite values, duplicate rows and engine-cycle keys, and cycle continuity. The quality summary in `reports/data_quality_summary.csv` records no missing cells, infinite cells, or duplicate engine-cycle keys in the eight source train/test tables. Training labels are computed from each engine's failure cycle; official test labels are mapped by engine for evaluation exports. An optional capped target (`RUL_capped_125`) is exported, but the reported models use uncapped RUL.

The training data alone determine which sensors are constant or near-constant (the most frequent value covers at least 95% of rows). The pipeline also creates one-cycle differences and five-cycle rolling means for sensors 2, 3, 4, 7, 11, 12, 15, and 21. A difference compares the present with the preceding cycle; a rolling mean summarizes the present and up to four earlier cycles. Neither uses future data. Model-ready export scaling fits mean and standard deviation on training data only and applies the same parameters to test data. The actual modeling workflow reloads the raw files and repeats selection inside each validation split, preventing held-out engine information from deciding the feature set.

## 4. What does the EDA show?

`reports/eda/engine_lifetimes.png` compares the distribution of observed engine lifetimes by subset; trajectories differ in length, so a row-random split would leak information from the same engine into training and validation. `reports/eda/fd001_sensor_trajectories.png` shows example sensor 2 and 11 readings through FD001 engine histories. These plots illustrate change over cycles, not proof that any one sensor diagnoses a failure. `reports/eda/sensor_variation.csv` supports the sensor-screening decision. `reports/eda/EDA_REPORT.md` explains the figures and counts.

## 5. What models were tested and why?

The median baseline always predicts the median training RUL; it checks whether a learned method improves on a simple constant guess. Ridge regression is regularized multiple linear regression: it represents a linear relationship between features and RUL, penalizes large coefficients, and fits standardization only on training data. Random Forest combines many regression trees fitted to varied samples/features, allowing nonlinear patterns and interactions. Histogram Gradient Boosting adds regression trees sequentially to reduce prior errors. These candidates fit the supplied course topics: regression, regularization, regression trees, bagging/random forests, and boosting. Neural networks, support vector regression, and logistic regression were not needed for this measured continuous-target comparison.

## 6. How was model selection separated from testing?

Within each FD subset, 20% of training engines are held out as validation engines using seed 42. One reproducible endpoint between 50% and 85% of each validation engine's observed lifetime simulates a partial-history test engine. Each candidate predicts RUL at those endpoints. Lowest validation RMSE chooses the model. The winner is then refitted on all training engines and used once at each official test engine's last cycle. No official test RUL is used in feature selection, fitting, hyperparameter choice, or winner selection. The engine IDs and model configuration are saved in `reports/modeling/FD00X/protocol.json`.

## 7. How should the scores be read?

MAE is the average absolute error in cycles; RMSE is the square root of average squared error, so large mistakes count more. Lower is better. R² compares squared error with predicting the test set's mean and can be negative, especially on small or shifted validation samples. Classification accuracy is not suitable for continuous RUL. The PHM asymmetric score is also saved, but raw scores should not be directly compared across subsets with different numbers of engines.

| Subset | Validation-selected model | Official test MAE | Official test RMSE | Official test R² |
| --- | --- | ---: | ---: | ---: |
| FD001 | Random Forest | 21.21 | 28.68 | 0.52 |
| FD002 | Histogram Gradient Boosting | 20.27 | 27.66 | 0.74 |
| FD003 | Histogram Gradient Boosting | 23.89 | 34.81 | 0.29 |
| FD004 | Histogram Gradient Boosting | 27.72 | 38.50 | 0.50 |

These are official-test scores, not training accuracy. FD002 has the lowest RMSE among the four recorded evaluations, but the subsets differ in operating conditions, fault modes, engine counts, and target distributions; a lower RMSE does not automatically make FD002 the universally easiest subset.

## 8. How should the figures be explained?

In each `reports/modeling/FD00X/official_test_actual_vs_predicted.png`, one point represents one test engine. Horizontal is true RUL and vertical is predicted RUL. The diagonal means exact prediction; above it the model overestimates life, below it underestimates life. The overestimate counts are FD001 65/100, FD002 150/259, FD003 76/100, and FD004 175/248. For maintenance interpretation, overestimation is especially concerning because the engine may have fewer safe cycles left than predicted. `reports/modeling/error_by_rul_band.png` groups absolute errors by true-RUL range; `reports/modeling/largest_official_test_errors.csv` gives individual mistakes. The plots explain error structure; the score table quantifies average performance.

## 9. What is the robustness check and limitation?

After the original official evaluation, `run_robustness.py` repeated a training-only engine split three times and scored held-out engines at 50%, 70%, and 85% of observed history. `reports/robustness/repeated_validation_rmse.png` shows mean RMSE and spread. Random Forest has the lowest mean RMSE for FD001, FD002, and FD004; boosting leads FD003. Thus the repeated-validation leader differs from the original winner in FD002 and FD004. The audit uses different endpoints and only three repeats, so it is a sensitivity check, not an unbiased replacement for the official-test decision or a confidence interval. The original official test was not retuned after seeing its answers.

Other limits: simulated data may not transfer to physical engines; initial wear and degradation onset are not directly known; long-lived engines contribute more training rows; one endpoint per validation engine creates selection noise; large individual errors remain. No model here should be used to approve real aircraft operation.

## 10. Reproduce and locate the evidence

After installing `requirements.txt`, run `run_pipeline.py`, `run_eda.py`, `train_models.py`, `run_error_analysis.py`, `run_robustness.py`, then `python3 -m unittest discover -s tests -v`. `data/processed/` is a regenerable local output folder. The reports, plots, protocol JSON files, notebook, and source code remain in the repository. The untouched source data remain in `data/raw/`; never edit them to make a plot or model run.

## References

1. Saxena, A., Goebel, K., Simon, D., and Eklund, N. (2008). Damage propagation modeling for aircraft engine run-to-failure simulation. DOI: 10.1109/PHM.2008.4711414.
2. Ramasso, E., and Saxena, A. (2014). Performance benchmarking and analysis of prognostic methods for C-MAPSS datasets. DOI: 10.36001/ijphm.2014.v5i2.2236.
