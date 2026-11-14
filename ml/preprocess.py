"""Load, clean, label-map and split network-flow data (CIC-IDS2017 format)."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from config import LABEL_COL, LABEL_RULES, RANDOM_STATE


def map_label(raw: str) -> str:
    """Map a raw label to a coarse class; unknown labels become 'Other'."""
    s = str(raw).strip().lower()
    for prefix, cls in LABEL_RULES:
        if s.startswith(prefix):
            return cls
    return "Other"


def load_csvs(path) -> pd.DataFrame:
    """Load one CSV or every CSV inside a directory."""
    path = Path(path)
    files = sorted(path.glob("*.csv")) if path.is_dir() else [path]
    if not files or not all(f.exists() for f in files):
        raise FileNotFoundError(f"No CSV data found at {path}. See data/README.md.")
    df = pd.concat([pd.read_csv(f, low_memory=False) for f in files], ignore_index=True)
    df.columns = [c.strip() for c in df.columns]  # CIC-IDS2017 headers have stray spaces
    if LABEL_COL not in df.columns:
        raise ValueError(f"Column '{LABEL_COL}' missing. Found: {list(df.columns)[:5]}...")
    return df


def clean(df: pd.DataFrame):
    """Return (X, y_multiclass, y_binary). Removes inf/NaN/duplicates."""
    df = df.replace([np.inf, -np.inf], np.nan).dropna().drop_duplicates()
    y = df[LABEL_COL].map(map_label)
    X = df.drop(columns=[LABEL_COL]).select_dtypes(include=[np.number]).astype("float64")
    yb = (y != "Benign").astype(int)
    return X.reset_index(drop=True), y.reset_index(drop=True), yb.reset_index(drop=True)


def split(X, y, yb, test_size=0.25):
    """Stratified train/test split on the multiclass label."""
    return train_test_split(X, y, yb, test_size=test_size, stratify=y, random_state=RANDOM_STATE)
