# Model selection against the supplied Machine Learning topic list

The supplied topic list is the boundary for model selection in this project. The task is supervised **regression**: predict remaining operating cycles from C-MAPSS settings and sensor history. Classification-only metrics and methods such as logistic regression, confusion matrices, precision, recall, and ROC curves are not primary measures for this continuous target. PCA or clustering could support exploratory work, but they are not required to predict RUL.

| Current candidate | Course topic | Role in this project |
| --- | --- | --- |
| Median predictor | Simple comparison baseline | Checks whether learned models improve on a trivial predictor. |
| Ridge regression | Multiple linear regression and L2 regularization | Interpretable regularized regression baseline. |
| Random Forest regressor | Regression trees, bagging, Random Forests | Nonlinear tree-ensemble candidate. |
| Histogram Gradient Boosting regressor | Regression trees and boosting | Nonlinear boosting candidate; the histogram algorithm is a software implementation detail, not a separate course topic. |

The engine-wise train/validation/test separation and error analysis also match the supplied topics. The current implementation does not use neural networks or deep learning. Model selection uses validation RMSE; official test labels are held back until evaluation.

## Why these models were chosen

Ridge gives a regularized linear reference. Random Forest and boosting test whether tree-based nonlinear relationships improve predictions. A median predictor shows the improvement over a trivial estimate. This is a compact comparison of techniques explicitly present in the supplied topic list; it does not require adding unrelated classifiers or advanced architectures.

## Status

- Done: NASA FD001–FD004 data provenance, preprocessing, EDA, syllabus-aligned baseline models, held-out evaluation, and error analysis.
- The model results are an evaluated academic prototype; real-aircraft deployment has not been validated.
