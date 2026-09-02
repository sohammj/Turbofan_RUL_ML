#!/usr/bin/env python3
"""Command-line entry point for the C-MAPSS preprocessing pipeline."""

from pathlib import Path

from src.cmapss_pipeline import run_pipeline


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    manifest = run_pipeline(root)
    print("Pipeline completed successfully.")
    print(f"Processed: {', '.join(manifest['datasets'])}")
    print(f"Merged sensors removed: {', '.join(manifest['merged_dropped_sensors'])}")
    print("See reports/PREPROCESSING_SUMMARY.md for verification evidence.")

