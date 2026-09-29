# Course-scope check (Machine Learning, 702DB0C015)

The course instruction plan is the boundary for model selection in this project. The task is supervised **regression**: predict remaining operating cycles from C-MAPSS settings and sensor history. Classification-only metrics and methods such as logistic regression, confusion matrices, precision, recall, and ROC curves are not primary measures for this continuous target. PCA or clustering could support exploratory work, but they are not required to predict RUL.

| Current candidate | Course topic | Role in this project |
| --- | --- | --- |
| Median predictor | Simple comparison baseline | Checks whether learned models improve on a trivial predictor. |
| Ridge regression | Multiple linear regression and L2 regularization | Interpretable regularized regression baseline. |
| Random Forest regressor | Regression trees, bagging, Random Forests | Nonlinear tree-ensemble candidate. |
| Histogram Gradient Boosting regressor | Regression trees and boosting | Nonlinear boosting candidate; the histogram algorithm is a software implementation detail, not a separate course topic. |

The engine-wise train/validation/test separation and error analysis also match the instruction plan. The current implementation does not use neural networks, deep learning, or an out-of-syllabus model. Model selection uses validation RMSE; official test labels are held back until evaluation.

## Important distinction: syllabus fit is not paper implementation

The course policy separately requires a 2–3-person group to **identify, understand, summarize, and implement a journal or IEEE-conference research paper**, with faculty approval of the topic/title. The current Ridge/forest/boosting comparison is a reproducible *baseline experiment*. Citing the 2008 C-MAPSS data-generation paper establishes the dataset's provenance, but it does **not** by itself demonstrate implementation of that paper's method. The existing report and presentation guide must not be described as satisfying the paper-implementation requirement yet.

Before course submission, the students should record (1) the faculty-approved paper and exact method selected, (2) which parts of its method were reproduced and which were changed, (3) a paper-versus-implementation comparison, (4) reproducible results and limitations, and (5) their own explanation of the code and decisions. Paper selection should remain within the taught topics above unless the faculty explicitly approves an extension. The course policy's academic-integrity and GenAI-use rules also apply; disclose assistance accurately and do not present generated code or prose as the students' independent work.

## Status

- Done: NASA FD001–FD004 data provenance, preprocessing, EDA, syllabus-aligned baseline models, held-out evaluation, and error analysis.
- Not yet established: faculty approval and a faithful implementation of a selected journal/IEEE research-paper method.
- Therefore: the repository is an evaluated baseline prototype, **not yet a completed course-policy submission**.
