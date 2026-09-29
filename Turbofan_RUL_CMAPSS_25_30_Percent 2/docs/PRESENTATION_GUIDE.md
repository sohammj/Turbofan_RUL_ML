# Presentation guide

This is a guide to the **baseline prototype**, not a claim that the separate course paper-implementation requirement is complete. Confirm faculty approval and the selected paper before presenting it as a final course project.

1. **Problem:** predict remaining operating cycles so maintenance can be planned earlier.
2. **Source:** NASA C-MAPSS is simulated turbofan data; show `data/raw/files/readme.txt` and one `train_FD001.txt` row.
3. **Schema:** 26 raw columns: engine, cycle, three settings, 21 sensors. Show `docs/DATA_DICTIONARY.md`.
4. **Preparation:** show `reports/PREPROCESSING_SUMMARY.md`, `reports/data_quality_summary.csv`, and the before/after samples. Explain RUL calculation and causal features.
5. **EDA:** show `reports/eda/engine_lifetimes.png` and `reports/eda/fd001_sensor_trajectories.png`.
6. **Model design:** show `docs/MODELING_PROTOCOL.md`. Stress engine-wise splitting and validation-only model selection.
7. **Results:** show the table in `docs/FINAL_PROJECT_REPORT.md` and `reports/modeling/FD001/official_test_actual_vs_predicted.png`.
8. **Limitations:** explain simulated data, negative validation R² on three subsets, and overestimation of remaining life.
9. **Reproducibility:** show `run_pipeline.py`, `run_eda.py`, `train_models.py`, `run_error_analysis.py`, tests, and the stage-by-stage Git history.

If asked whether this model is deployed, say that the deliverable is a reproducible research prototype with evaluated classical baselines. It is not validated for real maintenance decisions.
