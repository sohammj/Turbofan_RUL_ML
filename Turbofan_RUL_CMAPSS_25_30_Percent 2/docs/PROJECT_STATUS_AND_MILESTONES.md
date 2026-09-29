# Project status and milestones

## Audit on 29 September 2026

This repository contains the NASA C-MAPSS FD001–FD004 source archive, all twelve train/test/RUL text files, the source README, preprocessing code, processed outputs, provenance notes, and seven passing preprocessing tests. The four-subset project uses the standard C-MAPSS files; it is distinct from the original PHM08 challenge package named `train.txt`, `test.txt`, and `final_test.txt`.

The completed pipeline assigns the 26 input column names, checks data quality and cycle order, derives training RUL, attaches the official test RUL labels, audits low-information sensors, creates causal differences and rolling means, scales numerical features with training statistics, and exports subset and merged tables. These are data-preparation results. No model score or prediction is established by the preprocessing reports.

At audit time the working tree already contained user changes to `src/cmapss_pipeline.py`, generated reports, a large merged CSV, and `.DS_Store` files. These changes are intentionally outside this milestone's commits unless separately reviewed. The existing processed CSVs may have been generated before those changes; model evaluation should read the raw FD001 files and fit each transform within its own engine-wise training split.

## Remaining stages

1. **Exploratory analysis:** document engine lifetime, operating settings, sensor variation, and degradation trends, with reproducible figures or tables.
2. **Leakage-safe baseline:** split FD001 by engine, fit feature selection and scaling on training engines only, and compare a simple baseline with classical regressors.
3. **Held-out evaluation:** fit the selected approach on FD001 training trajectories and evaluate at the final observed cycle of each official test engine using `RUL_FD001.txt`. Report MAE, RMSE, and the PHM asymmetric score. Keep official RUL values out of predictors.
4. **Robustness:** repeat the same protocol for FD002–FD004 and compare performance by operating-condition and fault-mode complexity.
5. **Final package:** document methods, exact commands, data provenance, plots, results, limitations, and a concise college presentation.

Each completed stage should have a focused commit and a push to the configured GitHub remote. The commit message and report should identify what changed and which checks passed.

## Completion update on 29 September 2026

EDA, engine-wise classical-model validation, official held-out evaluation for all four subsets, and error analysis are now present. A draft research report is present, but the course submission is **not complete**: faculty approval and implementation of a selected journal/IEEE paper have not been established. The reproducible baseline results are in `reports/eda/` and `reports/modeling/`. See `docs/COURSE_SCOPE_AND_PAPER_REQUIREMENT.md` for the syllabus mapping and remaining requirement.
