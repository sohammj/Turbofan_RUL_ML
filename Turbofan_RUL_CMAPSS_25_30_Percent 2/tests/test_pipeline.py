"""Fast tests for the most important RUL and leakage invariants."""

import unittest

import pandas as pd

from src.cmapss_pipeline import (
    RAW_COLUMNS,
    apply_standardizer,
    attach_test_rul,
    attach_train_rul,
    fit_standardizer,
)


def tiny_frame() -> pd.DataFrame:
    rows = []
    for unit_id, length in ((1, 3), (2, 2)):
        for cycle in range(1, length + 1):
            rows.append([unit_id, cycle] + [0.0] * 24)
    return pd.DataFrame(rows, columns=RAW_COLUMNS)


class PipelineTests(unittest.TestCase):
    def test_training_rul_reaches_zero(self):
        result = attach_train_rul(tiny_frame())
        self.assertEqual(result.loc[result.unit_id == 1, "RUL"].tolist(), [2, 1, 0])
        self.assertEqual(result.loc[result.unit_id == 2, "RUL"].tolist(), [1, 0])

    def test_test_rul_vector_maps_to_last_observation(self):
        result = attach_test_rul(tiny_frame(), pd.Series([7, 11]))
        last = result[result.is_last_observation == 1].sort_values("unit_id")
        self.assertEqual(last.RUL.tolist(), [7, 11])
        self.assertEqual(result.loc[result.unit_id == 1, "RUL"].tolist(), [9, 8, 7])

    def test_train_fitted_scaler_is_reused(self):
        train = pd.DataFrame({"x": [0.0, 2.0]})
        test = pd.DataFrame({"x": [100.0]})
        params = fit_standardizer(train, ["x"])
        transformed = apply_standardizer(test, params, ["x"])
        self.assertEqual(float(transformed.loc[0, "x"]), 99.0)


if __name__ == "__main__":
    unittest.main()
