import unittest

import numpy as np
import pandas as pd

from train_models import make_features, phm_score, validation_endpoints
from run_robustness import FRACTIONS, partial_endpoints


class ModelingTests(unittest.TestCase):
    def test_validation_uses_one_partial_endpoint_per_engine(self):
        frame = pd.DataFrame(
            [(unit, cycle, 10 - cycle) for unit in (1, 2) for cycle in range(1, 11)],
            columns=["unit_id", "cycle", "RUL"],
        )
        endpoints = validation_endpoints(frame)
        self.assertEqual(len(endpoints), 2)
        self.assertTrue((endpoints["cycle"] < 10).all())
        self.assertTrue((endpoints["RUL"] > 0).all())

    def test_late_prediction_is_penalized_more(self):
        actual = np.array([50])
        self.assertGreater(phm_score(actual, np.array([60])), phm_score(actual, np.array([40])))

    def test_repeated_validation_uses_only_non_terminal_rows(self):
        frame = pd.DataFrame(
            [(unit, cycle, 10 - cycle) for unit in (1, 2) for cycle in range(1, 11)],
            columns=["unit_id", "cycle", "RUL"],
        )
        endpoints = partial_endpoints(frame)
        self.assertEqual(len(endpoints), 2 * len(FRACTIONS))
        self.assertTrue((endpoints["cycle"] < 10).all())
        self.assertTrue((endpoints["RUL"] > 0).all())

    def test_temporal_features_do_not_change_when_future_rows_are_added(self):
        early = pd.DataFrame({"unit_id": [1, 1, 1], "cycle": [1, 2, 3],
                              "sensor_2": [10.0, 12.0, 15.0]})
        later = pd.concat([early, pd.DataFrame({"unit_id": [1], "cycle": [4],
                                                "sensor_2": [99.0]})], ignore_index=True)
        early_features = make_features(early, ["sensor_2"])
        later_features = make_features(later, ["sensor_2"])
        for column in ("sensor_2_delta_1", "sensor_2_rolling_mean_5"):
            np.testing.assert_allclose(early_features[column], later_features[column].iloc[:3])


if __name__ == "__main__":
    unittest.main()
