# Repeated engine wise validation audit

`run_robustness.py` checks how sensitive the existing classical-model comparison is to an engine-wise split. It reads **training trajectories only**; no official test file or official RUL answer file enters this audit. Three `GroupShuffleSplit` repetitions hold out 20% of engines each time. At 50%, 70%, and 85% of each held-out engine's observed lifetime, the code makes a partial-history prediction using only current and earlier sensor readings. Sensor selection is recalculated from fitting engines in every repetition.

This is a **post-hoc stability analysis**, not a replacement for the earlier model-selection protocol. The original experiment used one randomly selected endpoint per held-out engine and chose its model before official-test evaluation. This audit uses three fixed endpoints per engine, so its validation scores are not directly interchangeable with the original validation scores. The official-test models and scores have not been changed after seeing the answer files.

| Subset | Lowest mean validation RMSE | Mean RMSE in cycles | Wins across three repetitions | Original official-test model |
| --- | --- | ---: | ---: | --- |
| FD001 | Random Forest | 24.90 | 2 | Random Forest |
| FD002 | Random Forest | 26.53 | 2 | Histogram Gradient Boosting |
| FD003 | Histogram Gradient Boosting | 38.01 | 3 | Histogram Gradient Boosting |
| FD004 | Random Forest | 38.77 | 3 | Histogram Gradient Boosting |

The mean-RMSE leader changes for FD002 and FD004 under this audit. That is evidence that winner selection depends on the validation design; it is **not** grounds to relabel the already-evaluated official-test results. In every subset, the tree ensembles outperform the median predictor by a large margin. For FD001, FD002, and FD004, the mean RMSE gap between Random Forest and boosting is small relative to their variation across repetitions. FD003 favors boosting in all three repetitions.

The exact scores are in `reports/robustness/repeated_validation_metrics.csv`, with means and standard deviations in `repeated_validation_summary.csv`, winner counts in `winner_counts.csv`, and split IDs and design choices in `split_protocol.json`. The `repeated_validation_rmse.png` figure shows mean RMSE with standard-deviation error bars. Three repetitions give a useful sensitivity check but do not establish a precise confidence interval or real-world reliability.
