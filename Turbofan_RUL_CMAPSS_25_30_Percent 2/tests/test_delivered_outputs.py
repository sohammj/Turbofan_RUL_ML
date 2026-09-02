"""Integration checks against the delivered processed evidence."""

import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class DeliveredOutputTests(unittest.TestCase):
    def test_expected_raw_files_are_present(self):
        raw = ROOT / "data" / "raw" / "files"
        for dataset_id in ("FD001", "FD002", "FD003", "FD004"):
            for prefix in ("train", "test", "RUL"):
                self.assertTrue((raw / f"{prefix}_{dataset_id}.txt").is_file())

    def test_all_quality_checks_are_clean(self):
        quality = pd.read_csv(ROOT / "reports" / "data_quality_summary.csv")
        for column in (
            "missing_cells",
            "exact_duplicate_rows",
            "duplicate_engine_cycle_keys",
            "infinite_numeric_cells",
        ):
            self.assertEqual(int(quality[column].sum()), 0)

    def test_all_rul_validations_pass(self):
        validations = pd.read_csv(ROOT / "reports" / "rul_validation_summary.csv")
        self.assertTrue(validations["passed"].all())
        self.assertTrue(
            (validations["expected_engine_rows"] == validations["observed_engine_rows"]).all()
        )

    def test_merged_files_have_dataset_id(self):
        merged = ROOT / "data" / "processed" / "merged"
        for name in (
            "train_all_subsets_model_ready.csv",
            "test_all_subsets_model_ready.csv",
        ):
            sample = pd.read_csv(merged / name, nrows=5)
            self.assertIn("dataset_id", sample.columns)
            self.assertIn("RUL", sample.columns)


if __name__ == "__main__":
    unittest.main()
