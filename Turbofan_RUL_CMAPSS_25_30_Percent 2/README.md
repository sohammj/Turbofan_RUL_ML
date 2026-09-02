# Predictive Remaining Useful Life Estimation of Aircraft Turbofan Engines

## First 25–30% milestone: data acquisition and preprocessing

This package is a reproducible college ML project milestone built from NASA's C-MAPSS Turbofan Engine Degradation Simulation Data Set. It contains all four subsets (FD001–FD004), untouched raw files, runnable preprocessing, RUL labels, leakage-safe scaling, causal starter features, merged files, evidence samples, data dictionaries, and project documentation.


## What is complete

- Official NASA PCoE C-MAPSS archive preserved under `data/raw/source_archive/`.
- Original train, test, RUL, and README files preserved byte-for-byte under `data/raw/files/`.
- All raw files covered by SHA-256 checksums in `reports/checksums_sha256.txt`.
- Explicit names assigned to 26 raw columns: engine ID, cycle, 3 settings, 21 sensors.
- Missing values, infinities, duplicates, key uniqueness, data types, and cycle ordering checked.
- Training row RUL calculated from each engine's final cycle.
- Official test RUL mapped by engine and expanded to every observed test cycle.
- Exact/near-constant sensors identified from training data only and decisions recorded.
- Training-only z-score parameters reused on test data to avoid leakage.
- Causal lag/delta and rolling features generated using no future cycles.
- Subset-level and all-subset model-ready/EDA-ready CSV files exported.

No predictive model has been trained in this milestone. That work belongs to the next phase.

## Run it

From this project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 run_pipeline.py
python3 -m unittest discover -s tests -v
```

The pipeline is idempotent: rerunning it recreates processed/report outputs from the preserved raw files.

## Best files to show the professor

1. `docs/PROJECT_REPORT_25_30_PERCENT.md` — problem, literature, scope, objectives, dataset, method, progress, references.
2. `docs/SOURCE_PROVENANCE.md` — exact source, hashes, retrieval route, and licensing note.
3. `notebooks/01_preprocessing_walkthrough.ipynb` — short, presentable walkthrough.
4. `src/cmapss_pipeline.py` — full practical implementation.
5. `reports/PREPROCESSING_SUMMARY.md` — automatically generated evidence and actual counts.
6. `reports/data_quality_summary.csv` — missing/duplicate/type checks.
7. `reports/feature_quality_by_subset.csv` — constant/near-constant sensor evidence.
8. `reports/before_after/` — raw, parsed, and processed samples.
9. `data/processed/merged/` — final merged train/test files.

## Folder map

```text
Turbofan_RUL_CMAPSS_25_30_Percent/
├── data/
│   ├── raw/
│   │   ├── source_archive/CMAPSSData.zip
│   │   └── files/                       # untouched NASA TXT + README
│   └── processed/
│       ├── by_subset/FD001...FD004/     # scaled model-ready CSVs + scalers
│       ├── eda_ready/                   # unscaled, labelled subset CSVs
│       └── merged/                      # merged FD001–FD004 train/test CSVs
├── docs/
│   ├── PROJECT_REPORT_25_30_PERCENT.md
│   ├── DATA_DICTIONARY.md
│   ├── DATA_DICTIONARY.csv
│   ├── SOURCE_PROVENANCE.md
│   └── Damage_Propagation_Modeling_2008.pdf
├── notebooks/01_preprocessing_walkthrough.ipynb
├── reports/
│   ├── PREPROCESSING_SUMMARY.md
│   ├── before_after/
│   └── CSV/JSON/checksum evidence
├── src/cmapss_pipeline.py
├── tests/test_pipeline.py
├── requirements.txt
└── run_pipeline.py
```

## Output conventions

- `dataset_id` distinguishes FD001–FD004 after merging because `unit_id` restarts at 1 in each subset.
- `RUL` is the uncapped, physically interpretable cycle count.
- `RUL_capped_125` is an optional piecewise-linear target commonly used in C-MAPSS experimentation; it does not replace the uncapped label.
- `rul_at_last_observation` exists only in labelled test exports and is evaluation ground truth, never a predictor.
- Metadata/label columns (`observed_last_cycle`, `true_failure_cycle`, `RUL`, capped RUL, terminal RUL, last-row flag) must not be used as model inputs.
- Model-ready numerical feature columns are z-scores. EDA-ready files remain unscaled for interpretation.

## Data provenance

- Official catalog: <https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data>
- NASA PCoE repository: <https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/>
- Retrieval mirror maintained by the PHM Society: <https://data.phmsociety.org/nasa/>
- Primary paper: <https://doi.org/10.1109/PHM.2008.4711414>

The current NASA legacy ZIP endpoint did not respond during packaging, so the byte-preserved NASA PCoE archive was retrieved from the PHM Society's NASA repository mirror. The included data are the NASA dataset, not a Kaggle re-upload.
