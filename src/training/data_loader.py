"""
SECTION 1: Header & Purpose
- Canonical dataset ingestion, validation, and splitting utilities for CodexHUB training workflows.
- Guarantees deterministic preprocessing aligned with governance requirements.
"""

from __future__ import annotations

# SECTION 2: Imports / Dependencies
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.common.config_loader import ConfigValidationError, DatasetConfig

# SECTION 3: Types / Interfaces / Schemas


@dataclass(frozen=True)
class DatasetSplits:
    """Container for deterministic train/validation splits."""

    x_train: pd.DataFrame
    x_validation: pd.DataFrame
    y_train: pd.Series
    y_validation: pd.Series
    sensitive_train: pd.Series | None = None
    sensitive_validation: pd.Series | None = None


# SECTION 4: Core Logic / Implementation


def load_dataset(config: DatasetConfig) -> pd.DataFrame:
    """Load dataset from disk using the provided dataset configuration."""

    dataset_path = Path(config.path)
    if not dataset_path.exists():
        msg = f"Dataset file not found at {dataset_path}"
        raise ConfigValidationError(msg)

    frame = pd.read_csv(dataset_path)
    missing_columns = _missing_required_columns(frame, config)
    if missing_columns:
        msg = f"Dataset is missing required columns: {sorted(missing_columns)}"
        raise ConfigValidationError(msg)

    feature_columns = config.feature_columns
    columns_to_use = feature_columns + [config.target_column]
    if config.sensitive_attribute:
        columns_to_use.append(config.sensitive_attribute)
    subset = frame.loc[:, columns_to_use].dropna()
    if subset.empty:
        raise ConfigValidationError("Dataset is empty after dropping NA rows")
    return subset


def split_dataset(config: DatasetConfig, dataset: pd.DataFrame) -> DatasetSplits:
    """Split dataset into training and validation subsets using stratified sampling when enabled."""

    x_data = dataset[config.feature_columns]
    y_data = dataset[config.target_column]

    stratify_target = y_data if config.stratify else None
    sensitive_data = (
        dataset[config.sensitive_attribute]
        if config.sensitive_attribute and config.sensitive_attribute in dataset
        else None
    )

    if sensitive_data is not None:
        try:
            x_train, x_val, y_train, y_val, s_train, s_val = train_test_split(
                x_data,
                y_data,
                sensitive_data,
                test_size=config.validation_split,
                random_state=config.random_state,
                stratify=stratify_target,
            )
        except ValueError:
            x_train, x_val, y_train, y_val, s_train, s_val = train_test_split(
                x_data,
                y_data,
                sensitive_data,
                test_size=config.validation_split,
                random_state=config.random_state,
                stratify=None,
            )
        return DatasetSplits(
            x_train=x_train,
            x_validation=x_val,
            y_train=y_train,
            y_validation=y_val,
            sensitive_train=s_train,
            sensitive_validation=s_val,
        )

    try:
        x_train, x_val, y_train, y_val = train_test_split(
            x_data,
            y_data,
            test_size=config.validation_split,
            random_state=config.random_state,
            stratify=stratify_target,
        )
    except ValueError:
        x_train, x_val, y_train, y_val = train_test_split(
            x_data,
            y_data,
            test_size=config.validation_split,
            random_state=config.random_state,
            stratify=None,
        )
    return DatasetSplits(x_train=x_train, x_validation=x_val, y_train=y_train, y_validation=y_val)


# SECTION 5: Error & Edge Case Handling
# - Missing dataset file raises ConfigValidationError.
# - Missing columns raise ConfigValidationError with explicit column names.
# - Empty datasets after NA removal trigger ConfigValidationError to signal upstream data issues.


# SECTION 6: Performance Considerations
# - Uses pandas vectorized operations for column selection and NA handling.
# - Relies on scikit-learn's efficient train_test_split which handles large datasets well.


# SECTION 7: Exports / Public API
__all__ = ["DatasetSplits", "load_dataset", "split_dataset"]


def _missing_required_columns(frame: pd.DataFrame, config: DatasetConfig) -> set[str]:
    """Identify any missing required columns for defensive validation."""

    required = set(config.feature_columns + [config.target_column])
    if config.sensitive_attribute:
        required.add(config.sensitive_attribute)
    present = set(frame.columns)
    return required.difference(present)
