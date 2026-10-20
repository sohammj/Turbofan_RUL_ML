# Predictive Remaining Useful Life Estimation of Aircraft Turbofan Engines

Machine Learning Group Activity Report

Program: B Tech Computer Science and Engineering Data Science  
Semester: V  
Course name and code: To be entered by the group  
Academic year: To be entered by the group  
Team name: To be entered by the group  
Mentor: Abhay Kolhe  
Submission date: To be entered by the group

| Group member | Roll number |
| --- | --- |
| Soham | To be entered |
| Hardik | To be entered |
| Farhaan | To be entered |
| Sanjeet | To be entered |
| Sparsh | To be entered |

## Declaration and individual contribution table

By signing below, each member confirms that the final submitted report accurately describes the work they performed and that cited material has been acknowledged. The division in Table 1 is the group activity allocation proposed for this project. It must be confirmed by the members before this page is signed or submitted as a declaration of completed individual work.

Table 1. Proposed group activity allocation

| Member | Assigned responsibility | Signature after confirmation |
| --- | --- | --- |
| Soham | Project integration, experiment protocol, final result interpretation, and report coordination. | __________ |
| Hardik | Dataset provenance, data dictionary, raw data inspection, and EDA interpretation. | __________ |
| Farhaan | Data quality, preprocessing, RUL label checks, and causal feature engineering. | __________ |
| Sanjeet | Candidate model explanation, model training, validation comparison, and reproducibility checks. | __________ |
| Sparsh | Official-test evaluation, prediction plots, error analysis, limitations, and presentation figures. | __________ |

## 1 Abstract

Predicting remaining useful life (RUL) from engine condition data could support better maintenance planning, but methods must separate training evidence from evaluation answers and must not imply operational safety from a simulated benchmark. This project studies NASA's C-MAPSS turbofan degradation data, covering FD001 through FD004. Each record contains an engine identifier, cycle, three operating settings, and 21 sensor measurements. The training trajectories continue to simulated failure, whereas the official test trajectories stop earlier. We checked source quality, derived cycle-level training RUL, screened low-variation sensors, generated one-cycle differences and five-cycle rolling means using only available history, and explored engine lifetimes and sensor trends. Four course-aligned regressors were compared: a median baseline, Ridge regression, Random Forest, and Histogram Gradient Boosting. A 20% engine-wise validation split selected the lowest-RMSE model independently for each subset. The selected model was refitted on all training engines and evaluated once against the official test RUL at each engine's final observed cycle. Test RMSE was 28.68, 27.66, 34.81, and 38.50 cycles for FD001, FD002, FD003, and FD004, respectively. Error analysis found frequent overestimation of remaining life; repeated training-only validation also changed the mean-RMSE leader in two subsets. The outcome is a reproducible classical-ML baseline with explicit leakage controls and documented limitations, not a maintenance decision system for real aircraft.

## 2 Introduction

### 2.1 Background and motivation

An aircraft engine gradually changes as components wear and operating conditions vary. A fixed maintenance interval may replace a component before its useful life ends, while an unexpected failure can disrupt schedules and require urgent maintenance. Prognostics estimates how long a system may operate before a defined end-of-life event. The present study uses simulated run-to-failure trajectories rather than claiming access to in-service aircraft engine records. Its purpose is methodological: to measure how well common regression methods estimate a numerical RUL target when only partial sensor history is available [1], [2].

The C-MAPSS benchmark is useful because it provides complete training trajectories, incomplete test trajectories, and held-out test RUL values. It also presents difficulties relevant to real prognostics: sensor noise, unequal engine lifetimes, different operating conditions, and multiple fault modes. Yet its simulation assumptions and limited scenarios mean that even a strong test score is not proof of field performance [1], [3].

### 2.2 Domain context

Condition-based maintenance can use sensor trends to prioritize inspections, but the cost of a RUL error is asymmetric. If predicted RUL exceeds true RUL, maintenance may be delayed too long. If predicted RUL is shorter than true RUL, maintenance may happen unnecessarily. The PHM scoring rule reflects this asymmetry, while MAE and RMSE describe the average size of prediction errors in cycles [2]. We therefore record both conventional regression metrics and the PHM score; we do not call regression performance classification accuracy.

### 2.3 Objectives

The objectives are to preserve and document the NASA source files; verify the integrity and structure of each data subset; generate RUL labels for training trajectories without using official test answers in fitting; explore lifetime and sensor patterns; engineer features that use only current and prior cycles; compare a simple baseline and three course-aligned regression models; select models on held-out engines; evaluate the selected models on the official test engines; and analyse error direction and stability across repeated validation splits.

### 2.4 Report organization

Section 3 reviews relevant work. Section 4 uses that literature to identify the study's focused research gaps. Sections 5 and 6 define the task and detail the data and modeling pipeline. Section 7 reports measured results and failure patterns. Sections 8 and 9 give conclusions and realistic extensions. The appendix links the executable evidence and source code.

## 3 Literature survey

The foundational C-MAPSS simulation study established the run-to-failure benchmark [1], while later benchmarking work cautioned that methods and evaluation choices affect comparisons [2]. Recent studies explore temporal neural networks, health indicators, feature selection, uncertainty, and explainability. Table 2 records the comparison at a level that can be verified from the papers. A reported numeric score is included only when the study, subset, and metric are identifiable. Its value must not be ranked directly against our uncapped-RUL result without checking target construction and evaluation protocol.

Table 2. Literature comparison for turbofan remaining useful life estimation

| Study | Technique and dataset | Reported result or metric | Limitation relevant here |
| --- | --- | --- | --- |
| Saxena et al., 2008 [1] | C-MAPSS run-to-failure simulation and PHM08 challenge formulation. | Defines test-engine RUL prediction benchmark. | Simulated degradation does not represent every physical engine or fault. |
| Ramasso and Saxena, 2014 [2] | Benchmark analysis of C-MAPSS prognostic methods. | Reviews scoring and method comparisons across C-MAPSS tasks. | Published scores depend on protocol and are not automatically comparable. |
| Ellefsen et al., 2019 [3] | Semi-supervised deep architecture on C-MAPSS. | Reports improved RUL prediction versus comparison methods. | Deep architecture and tuning increase complexity; simulation transfer remains open. |
| Hong et al., 2020 [4] | CNN, LSTM, Bi-LSTM, dimensionality reduction and SHAP on C-MAPSS. | Reports RUL prediction and feature explanations. | Explanations depend on model and feature representation. |
| Peng et al., 2021 [5] | Temporal and spatial feature fusion for FD001 and FD003. | Reports favorable RUL accuracy against comparison models. | Study covers two of the four classic subsets. |
| Wang et al., 2021 [6] | Temporal convolution and transformer combination on C-MAPSS. | Reports RUL prediction using selected sensors. | Deep sequence model is outside this project's implementation scope. |
| Mao et al., 2022 [7] | Differentiable neural architecture search on C-MAPSS. | Evaluates RUL error and PHM score. | Search adds optimization cost and reduces simplicity of reproduction. |
| Thakkar and Chaoui, 2022 [8] | Deep recurrent neural network on FD001. | Evaluates RUL from complete training and partial test histories. | FD001-only evaluation limits evidence for multi-condition subsets. |
| Liu et al., 2023 [9] | Sparse autoencoder plus temporal convolution on FD001. | FD001 RMSE 18.01 cycles and PHM score 161 under its protocol. | Target construction and preprocessing differ; direct ranking is invalid. |
| Ensarioğlu et al., 2023 [10] | Difference features, change-point target, CNN-LSTM on FD001. | Reports RMSE 16.1 cycles and score 437.2. | Added noise and alternative target definition hinder direct comparison. |
| Fan et al., 2024 [11] | Hierarchical attention transformer across FD001-FD004. | Reports RUL predictions for all four subsets. | Model complexity and interpretation remain concerns. |
| Salinas-Camus and Eleftheroglou, 2024 [12] | HMM and LSTM uncertainty analysis on C-MAPSS. | Examines predictive uncertainty rather than a single point score. | Different uncertainty sources are difficult to combine or calibrate. |
| Soualhi et al., 2024 [13] | Prognostic indicators and heterogeneous ML ensemble on C-MAPSS. | Reports improved score and prediction accuracy. | Indicator design and explanation add pipeline complexity. |

The survey reveals three recurring design choices. First, many high-performing methods use sophisticated sequence architectures, but these are harder to reproduce and explain than classical baselines [3], [6], [7], [9], [11]. Second, feature and target design change reported error substantially: low-variation sensor removal, temporal features, change-point labeling, and RUL capping are not interchangeable [4], [8], [10]. Third, literature increasingly treats uncertainty and interpretation as important alongside point error [4], [12], [13]. Our project therefore does not claim to outperform published methods. It tests a transparent, course-aligned baseline and reports the exact protocol needed to interpret its scores.

## 4 Research gaps

### 4.1 Comparability and leakage control

Benchmark papers often differ in target capping, window formation, sensor selection, and the exact rows on which RMSE is calculated [2], [9], [10]. A result table without these details can mislead. This study makes the selection boundary explicit: validation engines are held out as groups; sensor screening is fitted only on fitting engines; and official test answers are not used to choose a model. This does not solve all benchmarking differences, but it makes our own experiment auditable.

### 4.2 Simple methods as interpretable reference points

Recent sequence models report lower error in some configurations, but their architecture search, training setup, and feature attribution can be more involved [3], [6], [7], [11]. A median baseline, regularized linear model, bagged regression trees, and boosted trees establish what straightforward course-aligned methods achieve on the same four subsets. Their weakness is also informative: if a simple method overestimates life frequently, a low average RMSE alone is not a sufficient safety argument.

### 4.3 Uneven operating regimes and uncertain predictions

The FD002 and FD004 subsets include multiple operating conditions; FD003 and FD004 contain two fault modes. Studies on feature engineering and uncertainty show that operating regime and noise can affect RUL estimates [10], [12], [13]. Our original one-split selection may therefore be unstable. We add a separate repeated engine-wise validation audit and report that its mean-RMSE leader differs for FD002 and FD004. We do not retune the official-test models after observing those answers.

### 4.4 Scope of the gap addressed

The project does not claim a novel algorithm, calibrated uncertainty intervals, or real-world deployment. Its contribution is a reproducible reference experiment joining untouched source preservation, train-only feature decisions, course-scope regressors, official endpoint testing, and an honest stability and error-direction audit. That narrower contribution follows directly from the comparability and uncertainty concerns above.

## 5 Problem definition

### 5.1 Problem statement

Given an engine's observed operating settings and sensor measurements through cycle t, estimate the number of future operating cycles until the C-MAPSS simulation reaches its failure threshold. Each engine is a separate trajectory. Training trajectories have known failure cycles; official test trajectories end before failure. The predicted value is a nonnegative number of cycles.

### 5.2 Formal learning task

For engine i at cycle t, let x(i,t) contain the cycle index, three settings, retained sensor readings, one-cycle sensor differences, and five-cycle rolling means calculated only from cycles up to t. Let T(i) be the final training cycle. The supervised training target is y(i,t) = T(i) - t. A model f estimates y from x. At test time, the input is x(i,t_last), the final available test observation, and the answer is the official RUL supplied for that engine. This is regression; engine ID groups observations but is excluded from x. The final training cycle, test answer, and any derived label or last-observation metadata are also excluded from x.

### 5.3 Scope and assumptions

The scope is limited to FD001-FD004, their 21 simulated sensors, and the three operational settings. We treat each cycle as ordered within its engine and assume the training trajectory endpoint is the simulated failure event. We use uncapped RUL for reported models; a capped-125 export exists only as an optional alternative. No claim is made that these engine simulations are a representative sample of real aviation fleets. Maintenance actions, downtime, and costs are not optimized in this project.

### 5.4 Success criteria

The principal criterion is lower engine-level validation RMSE than the median baseline, followed by a separately reported official-test RMSE, MAE, and R². A complete result must also demonstrate no engine overlap between fitting and validation, no future-cycle information in temporal features, no official test answer in model selection, and a reproducible output record. An operational safety threshold is not specified because the dataset alone cannot justify one.

## 6 System design and methodology

### 6.1 Overall architecture

Figure 1 summarizes the process. The preprocessing export and model-selection experiment share the same untouched NASA source. The modeling script reloads raw files so validation-specific sensor decisions are made only after the engine split. This distinction prevents an EDA-ready export prepared on all training engines from quietly influencing held-out validation engines.

Figure 1. Project pipeline from untouched source to final evidence

SOURCE NASA TXT AND ZIP  ->  QUALITY CHECKS AND DATA DICTIONARY  ->  EDA AND CAUSAL FEATURES  ->  ENGINE-WISE VALIDATION  ->  MODEL SELECTION  ->  REFIT  ->  OFFICIAL TEST  ->  ERROR AND STABILITY AUDITS

### 6.2 Dataset selection

NASA's C-MAPSS dataset is public, has a well-defined numerical target, and includes complete training trajectories and early-stopped test trajectories [1]. Each raw row has 26 numeric fields: unit ID, cycle, three operational settings, and 21 sensor measurements. FD001 and FD003 represent one operating condition; FD002 and FD004 represent six. FD001 and FD002 have one fault mode; FD003 and FD004 have two. This variety tests whether a method behaves differently when operating regimes and failure patterns become more complex.

Table 3. Observed source dimensions and engine counts

| Subset | Train rows | Train engines | Test rows | Test engines | Conditions | Fault modes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FD001 | 20,631 | 100 | 13,096 | 100 | 1 | 1 |
| FD002 | 53,759 | 260 | 33,991 | 259 | 6 | 1 |
| FD003 | 24,720 | 100 | 16,596 | 100 | 1 | 2 |
| FD004 | 61,249 | 249 | 41,214 | 248 | 6 | 2 |

The dataset has no classification labels or class distribution. Its relevant distributions are engine lifetime, cycle count, RUL, and sensor values. Table 3 comes from `reports/dataset_summary.csv`. Figure 2 shows that full training lifetimes vary by engine and subset; this variation is why a random row split would provide an unrealistically easy validation problem.

Figure 2. Distribution of observed engine lifetimes by subset

![Engine lifetime distributions](reports/eda/engine_lifetimes.png)

The official source files are kept byte-for-byte in `data/raw/files/`; the original archive is in `data/raw/source_archive/`. Provenance and hashes are in `docs/SOURCE_PROVENANCE.md` and `reports/checksums_sha256.txt`. The repository models FD001-FD004, not the distinct PHM08 challenge package named `train.txt`, `test.txt`, and `final_test.txt`.

### 6.2.1 Source records and analytical units

A raw row is one observation of one simulated engine at one operating cycle. The first field identifies the engine within its subset, and the second field orders that engine's trajectory. They are not equivalent to two independent predictor measurements: the identifier is used for grouping, while the cycle number describes elapsed operational history. Fields three through five are the operating settings. The remaining 21 columns are simulator sensor channels, conventionally named sensor 1 through sensor 21. The raw text has no header row, so the pipeline supplies these column names after loading. Keeping the source file intact permits an examiner to show the original row layout separately from a labeled processed table.

The train file for a subset contains many rows per engine and ends at simulated failure. Accordingly, a training engine's total observed lifetime is its maximum recorded cycle. The test file also contains many rows per engine, but stops early; its final row is the prediction endpoint. The companion RUL answer file contains one value per test engine and is not a row-wise label for every test cycle. This difference is essential when counting samples: 53,759 FD002 training rows do not mean 53,759 independent engines, and 33,991 FD002 test rows produce only 259 official endpoint predictions. Evaluating all test rows against a repeated endpoint answer would misstate both the target and the sample size.

The four subset names should remain attached to every chart and metric. An engine ID of 1 in FD001 is not the same unit as engine ID 1 in FD002. The model fitting and evaluation processes are therefore run separately for each subset. The underlying benchmark supplies controlled variation in regime and fault complexity, but it does not supply real aircraft tail numbers, maintenance events, repair dates, or human safety outcomes. These absent fields cannot be inferred from the sensor traces. They are part of why the work is framed as a simulation-based regression study rather than an operational maintenance system.

### 6.3 Data preprocessing and feature engineering

The parser assigns names, converts columns to numeric form, verifies engine-cycle uniqueness, checks continuity within each trajectory, and counts missing values, infinite values, and duplicate rows. The saved quality report records zero missing cells, infinite cells, and duplicate engine-cycle keys across the eight source train/test tables. No values were imputed because these checks found no missing cells in those files. Training RUL is calculated from the final recorded cycle of each engine. The official RUL vector is associated with the corresponding test engine for evaluation only.

Low-information sensors are detected from the training partition: a sensor is removed if it is constant or if one value occupies at least 95% of fitting rows. The decision is re-estimated after the group split for validation and on all training engines for the final model. Temporal features are formed for sensors 2, 3, 4, 7, 11, 12, 15, and 21 when retained. The one-cycle difference captures short-term change, and the five-cycle rolling mean reduces local variation. Each uses only the present and earlier cycles. The first difference in an engine is filled with zero; the rolling mean uses available observations at the beginning of a trajectory.

The preprocessing export also provides standardized, model-ready CSVs. Its z-score parameters are fitted on training data and applied to test data. In the actual model comparison, Ridge uses its own `StandardScaler` fitted inside the training pipeline. The tree models do not require that scaling. No categorical encoding or synthetic augmentation is used. Figure 3 illustrates example FD001 sensor trajectories, while `reports/feature_quality_by_subset.csv` records the sensor-screening evidence.

Figure 3. Example FD001 sensor trajectories through operating cycles

![FD001 sensor trajectories](reports/eda/fd001_sensor_trajectories.png)

### 6.4 Model selection

Four candidates were chosen from the supplied course topics. The median baseline predicts a constant median RUL and gives an essential sanity check. Ridge is regularized multiple linear regression with an L2 penalty and training-only scaling. Random Forest averages many regression trees trained on varied samples and feature selections. Histogram Gradient Boosting adds regression trees sequentially to reduce previous errors. We did not train logistic regression because the target is continuous rather than binary.

Table 4. Model settings used in the experiment

| Candidate | Implementation and principal settings | Reason for inclusion |
| --- | --- | --- |
| Median baseline | `DummyRegressor(strategy=median)` | Minimum non-learning reference. |
| Ridge | `StandardScaler` plus `Ridge(alpha=10.0)` | Regularized linear reference. |
| Random Forest | 80 trees; minimum leaf 4; max features 0.8; seed 42 | Nonlinear bagged-tree candidate. |
| Histogram Gradient Boosting | 150 iterations; 31 max leaf nodes; L2 regularization 1.0; seed 42 | Sequential boosted-tree candidate. |

The hyperparameters were fixed before the official-test evaluation; no grid search or test-set tuning was performed. The candidate selected within each subset is the one with the smallest RMSE on its held-out training engines. If two models tied, validation MAE was the secondary sort key. This per-subset selection is appropriate because the four subsets have different regime and fault compositions.

The candidates address different modeling assumptions. Ridge represents a smooth weighted combination of available features. Its L2 penalty shrinks coefficients and can reduce instability when several sensors co-vary, but a single linear surface may not capture condition-dependent degradation. Random Forest partitions feature space into regions and averages predictions across trees. It can fit nonlinear interactions without manual polynomial terms, yet averaging may struggle to extrapolate beyond the RUL range or patterns well represented in its fitting data. Histogram Gradient Boosting also creates nonlinear regions but builds trees sequentially to correct residuals. That flexibility can improve error on a held-out sample, while still remaining sensitive to the validation design and fixed hyperparameters. The median baseline has no sensor dependence; beating it is necessary evidence that learned relationships add value, though it is not proof of reliable prognosis.

These descriptions explain why the models are useful comparisons rather than claims that one family is universally best. The validation decision is empirical and subset-specific. A 0.14-cycle RMSE difference between Random Forest and boosting on FD001 is much smaller than the size of an individual engine's error and should not be narrated as a decisive scientific finding. Likewise, the later robustness audit can reasonably change a model ranking without making the earlier official-test result invalid; it reveals sensitivity in the selection procedure. We retain both findings and identify which one produced the official-test prediction.

### 6.5 Model training

The implementation uses Python with NumPy, pandas, scikit-learn, and Matplotlib. The repository does not record a hardware specification, so no CPU, GPU, or training-time claim is made. `GroupShuffleSplit` with seed 42 holds out 20% of training engines. All cycles from one engine stay together. For each held-out engine, one endpoint sampled between 50% and 85% of its observed lifetime mimics a partial test history. All fitting rows are used to train the candidate model, while only one endpoint per validation engine is scored. This yields 20, 52, 20, and 50 validation engines for FD001-FD004.

Ridge minimizes squared error with an L2 coefficient penalty. The forest minimizes regression-tree split error within its ensemble. Histogram Gradient Boosting optimizes a squared-error regression objective through additive trees. The code uses fixed estimators/iterations rather than neural-network epochs or an explicit optimizer such as Adam. Regularization, minimum leaf size, feature subsampling, engine-wise splitting, and the held-out validation comparison constrain overfitting, but they cannot guarantee generalization. The original experiment has one validation split; repeated validation is reported separately as an audit, not used to select a different official-test model.

After selecting a winner, the script recomputes eligible sensors using all training engines, refits a fresh instance of that model on all training rows, and predicts at the last observed cycle of every official test engine. Negative numerical predictions are clipped to zero. The official test answer vector is read only for evaluation and the prediction tables record one row per test engine.

### 6.6 Reproducibility and leakage audit

The engine ID is a grouping key and not a predictive input. This matters because a row-level random split would place early and late observations from the same engine in both fitting and validation sets. Such a split would allow the model to exploit engine-specific patterns already seen during fitting and would not reproduce the official task of predicting a new engine from a truncated trajectory. The saved protocol lists the engines allocated to fitting and validation, making this boundary inspectable. The same seed and split rule can be rerun from the repository.

Sensor screening is another potential leakage point. A column that is nearly constant in the fitting engines might vary in held-out engines, or vice versa. If all training engines were screened before validation, the held-out distribution would influence which features are made available. The modeling workflow instead identifies eligible sensors on fitting rows, applies the resulting list to held-out rows, and only recomputes it on all training rows after the candidate has been chosen. Similarly, standardization for Ridge is inside the fitted model pipeline. The scaler learns its means and variances from fitting data and then transforms validation or test data without relearning them.

Temporal features obey a third boundary. At cycle t, a rolling mean uses cycles no later than t; a one-cycle difference compares t with the previous recorded cycle of the same engine. Neither feature sees the eventual failure cycle when it is calculated for a test engine. The failure cycle is needed only to make training labels. The official test RUL vector is intentionally separate from the predictors and can be used only after model selection and refitting. This separation is why the apparently similar processed export and model-training input have different roles: the export is useful for demonstration, whereas the modeling script rebuilds its validation-specific features from the original source.

For reproducibility, the repository saves row and engine counts, quality checks, chosen sensor sets, candidate metrics, model settings, final predictions, and diagnostic figures. A third party should be able to start from the original NASA archive, run the scripts in order, and compare the regenerated summaries with the values in this report. Small differences in regenerated numerical files may occur if dependency versions change, so the dependency list and the saved protocol should accompany any score claim. A score without its target definition, endpoint definition, and unit of evaluation is not fully reproducible.

### 6.7 Evaluation metrics

MAE is the mean absolute value of prediction error and is measured in cycles. RMSE is the square root of mean squared error; it penalizes large errors more heavily and is the model-selection metric. R² compares model squared error with a mean-prediction reference and may be negative on a difficult validation slice. The PHM score uses an asymmetric exponential penalty with a larger cost for overestimating remaining life, but its raw total also depends on the number of evaluated engines. Therefore, PHM scores should be compared only within the same subset and evaluation set. Accuracy, precision, recall, F1, ROC-AUC, confusion matrices, and ROC curves are classification tools and do not measure this continuous-RUL task.

## 7 Results and discussion

### 7.1 Exploratory findings

The dataset contains unequal engine lifetimes: the median full training trajectory is 199 cycles for FD001 and FD002, 220.5 for FD003, and 234 for FD004. The first and third subsets each have 100 test engines, whereas FD002 and FD004 have 259 and 248. Figure 2 therefore supports the choice of engine-wise evaluation and cautions against interpreting a raw PHM score across different sample sizes. Figure 3 shows that some sensor values change through time, but an illustrative trajectory is not itself a predictive model. Feature screening is computed rather than inferred visually.

### 7.2 Validation comparison of all candidates

Table 5 gives the original held-out-engine RMSE for all four candidates. The model with the lowest value in each subset was selected. Random Forest narrowly leads FD001; Histogram Gradient Boosting leads FD002-FD004. In FD001 the margin between the two tree candidates is only 0.14 cycles. FD004's tree-model margin is also small, approximately 0.19 cycles. Such small differences should not be described as strong evidence of an intrinsic algorithm advantage.

Table 5. Original validation RMSE in cycles for every candidate

| Subset | Median baseline | Ridge | Random Forest | Histogram Gradient Boosting | Selected |
| --- | ---: | ---: | ---: | ---: | --- |
| FD001 | 47.51 | 32.93 | 27.17 | 27.31 | Random Forest |
| FD002 | 47.55 | 41.37 | 33.14 | 32.16 | Histogram Gradient Boosting |
| FD003 | 67.43 | 53.09 | 28.13 | 24.87 | Histogram Gradient Boosting |
| FD004 | 58.79 | 56.47 | 45.38 | 45.19 | Histogram Gradient Boosting |

The baseline is worse than the selected model in every subset, satisfying the specified minimum learning criterion. However, validation R² is negative for FD001, FD002, and FD004. This means that this particular validation endpoint sample is challenging relative to its own mean-prediction reference even though the models improve on the median baseline. A negative validation R² must be reported, not hidden because official-test R² later appears positive.

### 7.3 Official test performance

The selected model was refitted on the full training subset and evaluated once at each official test engine endpoint. Table 6 reports these measured results. MAE and RMSE are in cycles. FD002 has the lowest recorded official-test RMSE among the four, but each subset has a different target distribution and operating scenario, so this does not establish that FD002 is inherently easier. FD004 has the largest test RMSE. The results are outcomes of the fixed experiment, not estimates of aircraft-level maintenance safety.

Table 6. Official test scores for validation-selected models

| Subset | Test engines | Selected model | MAE | RMSE | R² |
| --- | ---: | --- | ---: | ---: | ---: |
| FD001 | 100 | Random Forest | 21.21 | 28.68 | 0.52 |
| FD002 | 259 | Histogram Gradient Boosting | 20.27 | 27.66 | 0.74 |
| FD003 | 100 | Histogram Gradient Boosting | 23.89 | 34.81 | 0.29 |
| FD004 | 248 | Histogram Gradient Boosting | 27.72 | 38.50 | 0.50 |

Figure 4 displays official-test true versus predicted RUL for FD001 and Figure 5 for FD002. Each point is one test engine. The diagonal indicates exact prediction; points above it overestimate remaining life. The figures expose dispersion that a single RMSE cannot show. Some predictions at large true RUL are substantially below the diagonal, while a concentration of points at smaller RUL lies closer to it.

Figure 4. FD001 official test actual versus predicted RUL

![FD001 predictions](reports/modeling/FD001/official_test_actual_vs_predicted.png)

Figure 5. FD002 official test actual versus predicted RUL

![FD002 predictions](reports/modeling/FD002/official_test_actual_vs_predicted.png)

The four subsets should be read as four related experiments, not as four folds of one ordinary cross-validation run. They differ in conditions, fault modes, number of engines, and observed lifetime distributions. A lower RMSE in one subset does not imply that the corresponding model would be preferred in another subset. Even R² is relative to the variance of that subset's test answers. We therefore present within-subset model comparisons on the validation set and reserve the official test for the validation-selected model only.

Figure 6 and Figure 7 provide the corresponding endpoint views for FD003 and FD004. The paired plots make the two-fault-mode settings visible in the result discussion instead of relying on their table entries alone. Their diagonal remains the exact-prediction reference; distance from it is an individual engine's error. A trend line is not substituted for the actual one-engine-per-point evidence.

Figure 6. FD003 official test actual versus predicted RUL

![FD003 predictions](reports/modeling/FD003/official_test_actual_vs_predicted.png)

Figure 7. FD004 official test actual versus predicted RUL

![FD004 predictions](reports/modeling/FD004/official_test_actual_vs_predicted.png)

### 7.4 Error analysis

The selected model overestimated remaining life for 65 of 100 FD001 engines, 150 of 259 FD002 engines, 76 of 100 FD003 engines, and 175 of 248 FD004 engines. This direction matters because a late prediction could delay an inspection if the model were used operationally. Figure 8 groups mean absolute error by true-RUL band. Errors tend to be smaller for engines within 25 cycles of failure and larger for engines with long true remaining life, although the exact trend and sample count vary by subset. `reports/modeling/largest_official_test_errors.csv` lists the twenty largest individual errors; they should be reviewed before claiming any practical threshold.

The proportion of overestimates is not itself an accuracy metric. A model could overestimate often by a small amount or rarely by a very large amount. The saved prediction table permits both questions to be checked: count the sign of predicted minus true RUL and then inspect the magnitude of the signed errors. MAE treats both directions equally, RMSE amplifies large errors, and the PHM score penalizes late predictions more sharply. We report the sign counts because their operational meaning would be hidden by a symmetric average. We do not convert them into a decision threshold, since the project does not include the maintenance cost and risk information needed for such a threshold.

An actual maintenance decision would need at least three additional checks. First, the estimated RUL should be accompanied by a calibrated interval or conservative bound. Second, the policy should specify the consequences of early and late maintenance, not merely minimize numerical error. Third, the model would have to be validated on the engines and environments where it would be used. These checks are outside the present educational benchmark. Accordingly, the scatter plots and banded errors are diagnostic illustrations, not approval for operational use.

Figure 8. Mean absolute error by true remaining life band

![Error by RUL band](reports/modeling/error_by_rul_band.png)

### 7.5 Stability audit

A later training-only robustness audit repeated the engine-wise split three times and evaluated each held-out engine at fixed 50%, 70%, and 85% lifetime fractions. Figure 9 shows mean validation RMSE and its variation across repetitions. Random Forest has the lowest mean RMSE for FD001, FD002, and FD004, while Histogram Gradient Boosting leads FD003. Thus the audit differs from original selection for FD002 and FD004. It uses different endpoints and only three repetitions, so its mean is a sensitivity observation, not a confidence interval or an unbiased replacement for the original selection. Official test labels remained outside the audit, and the original official-test models were not switched after seeing their results.

This audit also illustrates why a single validation number should be interpreted with restraint. The original split samples one partial-history endpoint per held-out engine. The audit evaluates three fixed fractions and repeats the engine split. Changing both the engine selection and the length of available history changes the prediction task. A model that responds well to long histories may rank differently when the observations stop halfway through life. The audit therefore tests sensitivity to plausible evaluation choices; it does not mathematically estimate the uncertainty of the official test RMSE. A more rigorous future selection protocol would predefine repeated or nested group-wise validation, choose all model and feature decisions inside that protocol, and then evaluate the untouched official test exactly once.

Figure 9. Mean validation RMSE across three engine-wise splits

![Repeated validation RMSE](reports/robustness/repeated_validation_rmse.png)

### 7.6 Comparison with published results

The SAE-TCN paper reports FD001 RMSE 18.01 [9], and the change-point-labeling paper reports FD001 RMSE 16.1 [10], versus our FD001 official-test RMSE 28.68. These values demonstrate that other modeling and target choices can report lower error. They are not an apples-to-apples ranking: the studies differ in label construction, preprocessing, model class, and sometimes noise or evaluation details. Our report preserves uncapped RUL and a classical-model scope. A legitimate future benchmark comparison would rerun candidate methods under a common target definition, official endpoint set, feature availability rule, and tuning budget.

### 7.7 Limitations and ethical considerations

The source is simulated and may not transfer to different real engines, routes, maintenance histories, or sensor failures [1], [3]. The original model choice uses one engine-wise split and one endpoint per validation engine; three of four validation R² values are negative. All training rows are fitted, so long-lived engines contribute more examples. Hyperparameters were fixed rather than optimized. No calibrated uncertainty interval or cost-based maintenance decision rule is produced. Overestimation occurs frequently, and large individual errors remain. These limitations prevent any claim that the model is safe to deploy on aircraft.

The raw dataset contains simulated engines rather than personal data, so individual privacy is not the central issue. The relevant ethical risks are overstating safety, hiding unfavorable validation results, and presenting incomparable literature scores as direct competition. We address these risks by naming the simulation, retaining negative validation R², recording error direction, and separating our official-test results from published protocols. Any real deployment would require aviation-domain validation, safety review, uncertainty handling, and monitoring for data shift.

### 7.8 Threats to validity and interpretation

The first threat is the target itself. Training RUL is defined by the final recorded cycle of a simulated trajectory, not by a continuously observed physical failure process in commercial service. The benchmark's sensor-to-failure relation may be cleaner or differently noisy than an actual aircraft fleet. A model might learn simulator-specific correlations that disappear when sensors age, are recalibrated, or fail. Thus a useful benchmark score is evidence of performance under the benchmark assumptions only. It is not a certification, service-life warranty, or recommended interval for maintenance.

The second threat is sampling. The model fits all rows of the training trajectories, whereas the official test score uses one endpoint per engine. Long-lived engines therefore supply more fitting rows than short-lived engines. The group-wise split prevents the most direct engine leakage, but it does not equalize the influence of engines of different lengths. Moreover, the original held-out endpoints were sampled over a 50%–85% lifetime range. The official test endpoints may have a different distribution of truncation points. This mismatch can explain a difference between validation and official-test metrics without implying that one number is calculated incorrectly. Endpoint sampling and engine weighting deserve controlled study before drawing stronger conclusions.

The third threat is selection variability. Only one original split selected the submitted models, and the validation winner can change when the split and endpoint scheme change. Fixed hyperparameters keep the process auditable but may disadvantage one candidate more than another. The three-repetition audit is valuable as a warning, not enough to produce a precise confidence interval. Also, the four datasets are not four independent real-world fleets; they arise from related simulation assumptions. Averaging their RMSEs into a single headline number could conceal a serious weakness on the hardest subset.

Finally, the literature comparison is deliberately contextual. Published authors may cap RUL, select different sensors, choose different windows, tune with distinct budgets, or calculate scores on different units. Even when two studies use the label FD001, the numerical outcomes need not be directly ranked. Our 28.68-cycle FD001 RMSE is a clear measurement of our saved official-test predictions under our protocol. It is not an estimate that the best classical method is worse than every deep model, nor is the FD002 score evidence that the system generalizes to arbitrary operating conditions. A fair head-to-head comparison would rerun methods in one shared evaluation framework.

### 7.9 Evidence against the project objectives

Table 7 connects each major objective to evidence that a reviewer can open, rather than asking the reader to accept a narrative claim. It also distinguishes completed educational outputs from work that was deliberately not attempted. The table is not a second result set; its role is to make the project auditable during a presentation and to prevent a generated figure from being described as a completed deployment.

Table 7. Objective-to-evidence map

| Objective | Evidence available in the repository | Interpretation |
| --- | --- | --- |
| Preserve and inspect NASA data | Original archive, extracted files, source provenance, checksum record, and quality summaries. | Source can be inspected separately from processed CSVs. |
| Explore and prepare data | EDA figures, lifetime summaries, RUL checks, and feature-quality table. | Data structure and cleaning decisions are documented. |
| Compare course-scope models | Validation metrics for median, Ridge, Random Forest, and boosting in all four subsets. | Selection uses held-out training engines rather than test answers. |
| Evaluate chosen models | Official-test predictions, metrics, and actual-versus-predicted plots. | One prediction is scored per test engine endpoint. |
| Examine weaknesses | Error direction, RUL-band errors, largest errors, and repeated validation audit. | The report records instability and frequent life overestimation. |

Two boundaries remain important when showing these files. The processed tables are outputs of preprocessing and should not be mistaken for the untouched NASA download. Likewise, the model plots summarize an experiment but do not contain a trained aviation maintenance service. The reusable project artifact is the combination of source, scripts, configuration, tests, and generated evidence. If a team member reruns the workflow or updates one figure, the table and the surrounding claims must be rechecked against the new outputs before final submission. This is why the report keeps exact file locations and separates a proposed contribution allocation from a signed record of completed work.

## 8 Conclusion

The project built a reproducible classical machine-learning pipeline for NASA C-MAPSS RUL regression. Original source files were preserved, data quality was checked, training RUL was derived, causal sensor features were engineered, and EDA described lifetime and sensor variation. A held-out engine split selected Random Forest for FD001 and Histogram Gradient Boosting for FD002-FD004. All selected models improved validation RMSE over the median baseline; official-test RMSE ranged from 27.66 to 38.50 cycles. The post-hoc audit and error analysis qualify that result: model rankings vary with validation design, and remaining life is often overestimated. The project meets its educational aim of an auditable benchmark, not a real-aircraft maintenance system.

## 9 Future scope

Future work should use repeated nested engine-wise validation for model and hyperparameter selection while preserving the official test set as a one-time final check. The training objective could give each engine comparable weight, or sample endpoints to mirror the test task more closely. Evaluation should include uncertainty intervals and calibration, because a point estimate alone cannot express confidence [12]. A cost-sensitive objective could penalize life overestimation more heavily, with thresholds chosen by maintenance experts rather than from this dataset alone. External datasets, including different simulated regimes and eventually carefully governed operational records, would be necessary to study transfer. Feature attribution could be added with checks that explanations remain stable across engines and conditions [4], [13].

## 10 References

[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, “Damage propagation modeling for aircraft engine run-to-failure simulation,” in Proc. Int. Conf. Prognostics and Health Management, 2008, doi: 10.1109/PHM.2008.4711414.

[2] E. Ramasso and A. Saxena, “Performance benchmarking and analysis of prognostic methods for C-MAPSS datasets,” Int. J. Prognostics and Health Management, 2014, doi: 10.36001/ijphm.2014.v5i2.2236.

[3] A. L. Ellefsen, E. Bjørlykhaug, V. Æsøy, S. Ushakov, and H. Zhang, “Remaining useful life predictions for turbofan engine degradation using semi-supervised deep architecture,” Reliability Engineering and System Safety, vol. 183, pp. 240–251, 2019, doi: 10.1016/j.ress.2018.11.027.

[4] C. W. Hong et al., “Remaining useful life prognosis for turbofan engine using explainable deep neural networks with dimensionality reduction,” Sensors, vol. 20, no. 22, Art. 6626, 2020, doi: 10.3390/s20226626.

[5] C. Peng et al., “A remaining useful life prognosis of turbofan engine using temporal and spatial feature fusion,” Sensors, vol. 21, no. 2, Art. 418, 2021, doi: 10.3390/s21020418.

[6] H.-K. Wang, Y. Cheng, and K. Song, “Remaining useful life estimation of aircraft engines using a joint deep learning model based on TCNN and Transformer,” Computational Intelligence and Neuroscience, 2021, doi: 10.1155/2021/5185938.

[7] P. Mao, Y. Lin, S. Xue, and B. Zhang, “Remaining useful life estimation of aircraft engines using differentiable architecture search,” Mathematics, vol. 10, no. 3, Art. 352, 2022, doi: 10.3390/math10030352.

[8] U. R. Thakkar and H. Chaoui, “Remaining useful life prediction of an aircraft turbofan engine using deep layer recurrent neural networks,” Actuators, vol. 11, no. 3, Art. 67, 2022, doi: 10.3390/act11030067.

[9] X. Liu, L. Xiong, Y. Zhang, and C. Luo, “Remaining useful life prediction for turbofan engine using SAE-TCN model,” Aerospace, vol. 10, no. 8, Art. 715, 2023, doi: 10.3390/aerospace10080715.

[10] K. Ensarioğlu, T. İnkaya, and E. Emel, “Remaining useful life estimation of turbofan engines with deep learning using change-point detection based labeling and feature engineering,” Applied Sciences, vol. 13, no. 21, Art. 11893, 2023, doi: 10.3390/app132111893.

[11] Z. Fan, W. Li, and K.-C. Chang, “A two-stage attention-based hierarchical transformer for turbofan engine remaining useful life prediction,” Sensors, vol. 24, no. 3, Art. 824, 2024, doi: 10.3390/s24030824.

[12] M. Salinas-Camus and N. Eleftheroglou, “Uncertainty in aircraft turbofan engine prognostics on the C-MAPSS dataset,” PHM Society European Conference, vol. 8, 2024, doi: 10.36001/phme.2024.v8i1.4007.

[13] M. Soualhi, K. T. P. Nguyen, and K. Medjaher, “Explainable RUL estimation of turbofan engines based on prognostic indicators and heterogeneous ensemble machine learning predictors,” Engineering Applications of Artificial Intelligence, vol. 133, Art. 108186, 2024, doi: 10.1016/j.engappai.2024.108186.

## Appendix A Repository and reproducibility

Repository: https://github.com/sohammj/Turbofan_RUL_ML. The exact source archive and checksum record are in `data/raw/` and `reports/checksums_sha256.txt`. The code modules are `run_pipeline.py`, `run_eda.py`, `train_models.py`, `run_error_analysis.py`, `run_robustness.py`, and `src/cmapss_pipeline.py`. The saved CSVs, PNGs, and protocol JSON files under `reports/` are the evidence for the tables and figures above. Generated large CSVs in `data/processed/` are local-only and can be recreated with `run_pipeline.py`.

From the project folder, install `requirements.txt`, run the five stage scripts in the sequence above, and run `python3 -m unittest discover -s tests -v`. Eleven automated checks passed in the project environment at the time of report preparation. Re-running stages may change generated timestamps or floating-point least-significant digits; inspect changes before making a new Git commit. The official-test answer files are present locally for evaluation, but they must remain excluded from candidate selection and feature fitting.

## Appendix B Additional result locations

The validation metrics for every candidate are in `reports/modeling/FD00X/validation_metrics.csv`. Each chosen model's official-test metrics and one-row-per-engine predictions are in the corresponding `official_test_metrics.csv` and `official_test_predictions.csv`. `protocol.json` records validation engine IDs, random seed, selected sensors, and the selected model. `reports/modeling/error_direction_counts.csv`, `error_by_rul_band.csv`, and `largest_official_test_errors.csv` support the error analysis. `reports/robustness/repeated_validation_summary.csv` and the associated figure support the sensitivity discussion. These paths make every reported project number traceable to a saved output.
