import io
import pandas as pd
import numpy as np
import streamlit as st

def load_datasets(uploaded_files):
    datasets = {}
    for f in uploaded_files:
        raw = f.getvalue()
        if f.name.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw))
        elif f.name.lower().endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(raw))
        else:
            raise ValueError(f"Unsupported file: {f.name}")

        if df.empty:
            raise ValueError(f"{f.name} is empty.")
        datasets[f.name] = df.copy()
    return datasets

def _date_candidates(df):
    candidates = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            candidates.append(col)
            continue
        if df[col].dtype == "object":
            sample = df[col].dropna().head(100)
            if len(sample):
                parsed = pd.to_datetime(sample, errors="coerce")
                if parsed.notna().mean() >= 0.8:
                    candidates.append(col)
    return candidates

def profile_dataframe(name, df):
    numeric = df.select_dtypes(include=np.number).columns.tolist()
    categorical = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    dates = _date_candidates(df)
    unique = {str(c): int(df[c].nunique(dropna=True)) for c in df.columns}
    missing = {str(c): int(df[c].isna().sum()) for c in df.columns}

    stats = {}
    if numeric:
        desc = df[numeric].describe().replace({np.nan: None})
        stats = desc.to_dict()

    return {
        "name": name,
        "rows": int(len(df)),
        "columns_count": int(len(df.columns)),
        "columns": [str(c) for c in df.columns],
        "dtypes": {str(c): str(df[c].dtype) for c in df.columns},
        "missing": missing,
        "missing_percentage": {
            str(c): round(float(df[c].isna().mean() * 100), 2) for c in df.columns
        },
        "duplicates": int(df.duplicated().sum()),
        "unique_values": unique,
        "numeric_columns": numeric,
        "categorical_columns": categorical,
        "date_columns": dates,
        "statistics": stats,
        "sample": df.head(5).astype(str).to_dict(orient="records"),
    }

def build_profiles(datasets):
    return {name: profile_dataframe(name, df) for name, df in datasets.items()}
