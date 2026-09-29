import unittest

import numpy as np
import pandas as pd

from train_models import phm_score, validation_endpoints


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


if __name__ == "__main__":
    unittest.main()
