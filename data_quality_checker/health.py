"""Read tabular data, normalize safe formatting issues, and build a report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_table(source: Path) -> pd.DataFrame:
    suffix = source.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source)
    if suffix == ".xlsx":
        return pd.read_excel(source)
    raise ValueError("Supported inputs are CSV, XLSX, and XLSM files.")


def clean_table(frame: pd.DataFrame, drop_duplicates: bool = True) -> tuple[pd.DataFrame, int]:
    cleaned = frame.copy()
    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        cleaned[column] = cleaned[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
        cleaned[column] = cleaned[column].replace("", pd.NA)
    duplicate_count = int(cleaned.duplicated().sum())
    if drop_duplicates:
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    return cleaned, duplicate_count


def column_profile(frame: pd.DataFrame) -> list[dict[str, object]]:
    profiles = []
    row_count = len(frame)
    for column in frame.columns:
        series = frame[column]
        missing = int(series.isna().sum())
        non_empty = series.dropna()
        unique_count = int(series.nunique(dropna=True))
        date_like = any(token in str(column).lower() for token in ("date", "time", "created", "updated"))
        date_issue = ""
        if date_like and len(non_empty):
            parsed = pd.to_datetime(non_empty, errors="coerce")
            invalid = int(parsed.isna().sum())
            if invalid:
                date_issue = f"{invalid} non-date value(s)"
        profiles.append(
            {
                "column": str(column),
                "dtype": str(series.dtype),
                "missing": missing,
                "missing_pct": round((missing / row_count * 100) if row_count else 0, 1),
                "unique": unique_count,
                "date_issue": date_issue,
            }
        )
    return profiles


def make_report(
    source: Path,
    original: pd.DataFrame,
    cleaned: pd.DataFrame,
    duplicates: int,
) -> str:
    profile = pd.DataFrame(column_profile(original))
    table = profile.to_markdown(index=False) if not profile.empty else "_No columns found._"
    dropped = len(original) - len(cleaned)
    return "\n".join(
        [
            "# Data Health Report",
            "",
            f"- **Source:** {source.name}",
            f"- **Rows:** {len(original)}",
            f"- **Columns:** {len(original.columns)}",
            f"- **Exact duplicate rows:** {duplicates}",
            f"- **Rows removed from cleaned copy:** {dropped}",
            "",
            "## Column profile",
            "",
            table,
            "",
            "## Cleaning applied",
            "",
            "- Leading and trailing whitespace was removed from text cells.",
            "- Empty text cells were normalized to missing values.",
            "- Exact duplicate rows were removed unless the keep-duplicates option was used.",
            "- Missing values are reported, not filled with guessed values.",
            "",
        ]
    )


def save_table(frame: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.suffix.lower() == ".csv":
        frame.to_csv(destination, index=False)
    elif destination.suffix.lower() == ".xlsx":
        frame.to_excel(destination, index=False)
    else:
        raise ValueError("Output extension must be CSV, XLSX, or XLSM.")
