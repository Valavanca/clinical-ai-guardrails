from __future__ import annotations

from pathlib import Path
from typing import Union, Tuple, List

import pandas as pd
import numpy as np

from smolagents import Tool


def _resolve(path_like: Union[str, Path]) -> Path:
    path = Path(path_like).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() != ".csv":
        raise ValueError(f"{path} is not a .csv file")
    return path


class LoadCSVDatasetTool(Tool):
    name = "load_csv_dataset"
    description = """
    Load a feature matrix X and target vector y from two separate CSV files.
    The tool handles alignment of rows if an ID column is provided and can
    automatically detect the target column in simple cases.
    """
    inputs = {
        "X_path": {
            "type": "string",
            "description": "Path to the feature CSV file.",
        },
        "y_path": {
            "type": "string",
            "description": "Path to the label CSV file.",
        },
        "id_col": {
            "type": "string",
            "description": "Name/position of a shared identifier column (e.g., 'id', 0). If given, rows are aligned via an inner join on this column.",
            "default": None,
            "nullable": True,
        },
        "target_col": {
            "type": "string",
            "description": "Name/position of the actual label column inside y_path. If omitted and y-file has exactly one non-ID column, that column is used automatically.",
            "default": None,
            "nullable": True
        },
        "na_values": {
            "type": "string",
            "description": "Values to interpret as NaN when reading CSV files.",
            "default": None,
            "nullable": True
        },
        "dtype_backend": {
            "type": "string",
            "description": "Backend to use for pandas.read_csv dtype processing.",
            "default": None,
            "nullable": True
        }
    }
    output_type = "array"
    
    def forward(
        self,
        X_path: Union[str, Path],
        y_path: Union[str, Path],
        *,
        id_col: str | int | None = None,       
        target_col: str | int | None = None,   
        na_values: List[str] | None = None,
        dtype_backend: str | None = None,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Load a feature matrix X and target vector y from two separate CSVs.

        Args:
            X_path: Path to the feature CSV file.
            y_path: Path to the label CSV file.
            id_col: Name/position of a shared identifier column (e.g., "id", 0).
                If given, rows are aligned via an inner join on this column.
                If None (default) the two files are assumed to be in identical order.
            target_col: Name/position of the actual label column inside y_path.
                If the y-file has exactly one non-ID column, it is used
                automatically and target_col may be omitted.
                Otherwise this argument is required.
            na_values: Values to interpret as NaN when reading CSV files.
            dtype_backend: Backend to use for pandas.read_csv dtype processing.

        Returns:
            Tuple containing:
            - X: Feature matrix as ndarray (n_samples, n_features)
            - y: Target vector as ndarray (n_samples,)
            - feature_names: List of feature column names

        Raises:
            FileNotFoundError: If the CSV files don't exist
            ValueError: If alignment fails or required columns aren't found
        """
        # 1) read both files -----------------------------------------------------------------
        X_df = pd.read_csv(_resolve(X_path), na_values=na_values,
                        dtype_backend=dtype_backend)
        y_df = pd.read_csv(_resolve(y_path), na_values=na_values,
                        dtype_backend=dtype_backend)

        # 2) align on ID if requested ---------------------------------------------------------
        if id_col is not None:
            if id_col not in X_df.columns or id_col not in y_df.columns:
                raise ValueError(f"'{id_col}' column must exist in both CSVs")
            X_df = X_df.set_index(id_col)
            y_df = y_df.set_index(id_col)
            # inner-join to keep only rows present in *both*
            X_df, y_df = X_df.align(y_df, join="inner", axis=0)

        # 3) pick the target column -----------------------------------------------------------
        non_id_cols = [c for c in y_df.columns if c != id_col]
        if target_col is None:
            if len(non_id_cols) != 1:
                raise ValueError(
                    "y CSV has multiple candidate columns; specify `target_col`")
            target_col = non_id_cols[0]

        if target_col not in y_df.columns:
            raise ValueError(f"target_col '{target_col}' not found in {y_path}")

        y_arr = y_df[target_col].to_numpy()
        X_arr = X_df.to_numpy()
        if X_arr.shape[0] != y_arr.shape[0]:
            raise ValueError("After alignment, X and y have different #rows")

        feature_names: List[str] = X_df.columns.tolist()
        return X_arr, y_arr, feature_names


class SummarizeDatasetTool(Tool):
    name = "summarize_dataset"
    description = """
    Generate a Markdown summary describing the contents of a CSV dataset.
    The summary includes dimensions, missing values, numeric feature statistics,
    categorical level distributions, and target variable summary.
    """
    inputs = {
        "csv_path": {
            "type": "string",
            "description": "Path to the CSV file to summarize.",
        },
        "target": {
            "type": "string",
            "description": "Name of the target column in the dataset.",
        },
        "sample": {
            "type": "integer",
            "description": "Number of rows to randomly sample for a faster summary.",
            "default": None,
            "nullable": True,
        },
        "seed": {
            "type": "integer",
            "description": "Random seed used when sampling.",
            "default": None,
            "nullable": True
        },
        "max_levels": {
            "type": "integer",
            "description": "Maximum category levels to display per categorical column.",
            "default": 3,
            "nullable": False
        }
    }
    output_type = "string"
    
    def forward(
        self,
        csv_path: Union[str, Path],
        target: str,
        *,
        sample: int | None = None,
        seed: int | None = None,
        max_levels: int = 3,
    ) -> str:
        """Return a Markdown summary describing the dataset at csv_path.

        Args:
            csv_path: Path to the CSV file.
            target: Target column name.
            sample: If given, randomly sample this many rows for a faster first look.
            seed: RNG seed used when sample is specified.
            max_levels: Maximum category levels to display per categorical column.
                Defaults to 3.

        Returns:
            A human-readable Markdown document summarizing the dataset.
            
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            ValueError: If the target column is not found in the dataset
        """
        path = _resolve(csv_path)

        rng = np.random.default_rng(seed)
        df = pd.read_csv(path)

        if sample is not None and 0 < sample < len(df):
            df = df.sample(sample, random_state=rng.integers(0, 2**32 - 1))

        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not found in dataset")

        # General info -----------------------------------------------------------
        n_rows, n_cols = df.shape
        n_missing = df.isna().sum().sum()
        perc_missing = n_missing / (n_rows * n_cols) * 100.0

        lines: list[str] = []
        lines.append(f"# Dataset Summary\n")
        lines.append(f"*Samples*: **{n_rows}**  |  *Features*: **{n_cols - 1}**  |  *Missing values*: **{n_missing} ({perc_missing:.2f}% )**\n")

        # Numeric features -------------------------------------------------------
        num_df = df.select_dtypes(include=["number"]).drop(columns=[target], errors="ignore")
        if not num_df.empty:
            desc = num_df.describe().T  # index=feature, columns=['count','mean',...]
            lines.append("\n## Numeric Features\n")
            lines.append(desc.to_markdown(floatfmt=".3f"))

        # Categorical features ----------------------------------------------------
        cat_df = df.select_dtypes(include=["object", "category", "string"]).drop(columns=[target], errors="ignore")
        if not cat_df.empty:
            lines.append("\n## Categorical Features\n")
            for col in cat_df.columns:
                vc = cat_df[col].value_counts(dropna=False)
                top = vc.iloc[:max_levels]
                others = vc.iloc[max_levels:].sum()
                md = ", ".join([f"{k}: {v}" for k, v in top.items()])
                if others:
                    md += f", others: {others}"
                lines.append(f"* **{col}** – {md}")

        # Target summary ---------------------------------------------------------
        y = df[target]
        lines.append("\n## Target Summary\n")
        if pd.api.types.is_numeric_dtype(y):
            lines.append(y.describe().to_markdown(floatfmt=".3f"))
        else:
            vc = y.value_counts(dropna=False)
            lines.append(vc.to_markdown())

        return "\n".join(lines)