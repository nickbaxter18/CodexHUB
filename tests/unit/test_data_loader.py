"""
SECTION 1: Header & Purpose
- Tests for dataset loading and splitting utilities.
"""

# SECTION 2: Imports / Dependencies
from pathlib import Path

import pandas as pd
import pytest

from src.common.config_loader import ConfigValidationError, DatasetConfig
from src.training.data_loader import DatasetSplits, load_dataset, split_dataset

# SECTION 3: Types / Interfaces / Schemas
# - Utilizes DatasetConfig for configuration validation in tests.

# SECTION 4: Core Logic / Implementation


def _create_sample_csv(tmp_path: Path) -> Path:
    data = pd.DataFrame(
        {
            "feature_one": [1, 2, 3, 4],
            "feature_two": [0.1, 0.3, 0.2, 0.5],
            "label": [0, 1, 0, 1],
        }
    )
    csv_path = tmp_path / "dataset.csv"
    data.to_csv(csv_path, index=False)
    return csv_path


def test_load_dataset_success(tmp_path: Path) -> None:
    csv_path = _create_sample_csv(tmp_path)
    config = DatasetConfig(
        path=csv_path,
        target_column="label",
        feature_columns=["feature_one", "feature_two"],
        validation_split=0.25,
        stratify=True,
        random_state=7,
    )
    dataset = load_dataset(config)
    assert not dataset.empty
    assert list(dataset.columns) == ["feature_one", "feature_two", "label"]


def test_load_dataset_missing_column(tmp_path: Path) -> None:
    csv_path = _create_sample_csv(tmp_path)
    config = DatasetConfig(
        path=csv_path,
        target_column="label_missing",
        feature_columns=["feature_one", "feature_two"],
        validation_split=0.2,
        stratify=False,
        random_state=1,
    )
    with pytest.raises(ConfigValidationError):
        load_dataset(config)


def test_split_dataset_stratified(tmp_path: Path) -> None:
    csv_path = _create_sample_csv(tmp_path)
    config = DatasetConfig(
        path=csv_path,
        target_column="label",
        feature_columns=["feature_one", "feature_two"],
        validation_split=0.25,
        stratify=True,
        random_state=42,
    )
    dataset = load_dataset(config)
    splits = split_dataset(config, dataset)
    assert isinstance(splits, DatasetSplits)
    assert len(splits.x_train) + len(splits.x_validation) == len(dataset)


# SECTION 5: Error & Edge Case Handling
# - Tests missing target column raising an exception.
# - Confirms stratified split maintains dataset size.


# SECTION 6: Performance Considerations
# - Uses small synthetic dataset ensuring quick execution.


# SECTION 7: No exports required for test module.
