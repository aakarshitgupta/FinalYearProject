from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split


REQUIRED_COLUMNS = {"text", "label"}


@dataclass
class DataBundle:
    dataset: DatasetDict
    label_counts: dict[int, int]


def load_dataframe(data_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Dataset is missing required columns: {missing_text}")

    df = df[["text", "label"]].dropna()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""].copy()
    df["label"] = df["label"].astype(int)
    return df


def build_dataset(data_path: str | Path, test_size: float = 0.2, seed: int = 42) -> DataBundle:
    df = load_dataframe(data_path)
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=seed,
        stratify=df["label"] if df["label"].nunique() > 1 else None,
    )

    dataset = DatasetDict(
        {
            "train": Dataset.from_pandas(train_df.reset_index(drop=True)),
            "test": Dataset.from_pandas(test_df.reset_index(drop=True)),
        }
    )
    label_counts = {int(k): int(v) for k, v in df["label"].value_counts().sort_index().items()}
    return DataBundle(dataset=dataset, label_counts=label_counts)
