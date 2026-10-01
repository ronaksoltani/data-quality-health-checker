"""Command-line interface for dataset health checks."""

from __future__ import annotations

import argparse
from pathlib import Path

from .health import clean_table, load_table, make_report, save_table


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Profile, normalize, and report on a CSV or Excel file.")
    result.add_argument("input", type=Path)
    result.add_argument("--output", type=Path, help="Cleaned file path; defaults beside the source")
    result.add_argument("--report", type=Path, help="Markdown report path; defaults beside the source")
    result.add_argument("--keep-duplicates", action="store_true", help="Report duplicates but keep them")
    return result


def main() -> int:
    args = parser().parse_args()
    source = args.input.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Input file does not exist: {source}")
    suffix = source.suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise SystemExit("Supported inputs are CSV and XLSX files.")
    output = args.output.expanduser().resolve() if args.output else source.with_name(
        f"{source.stem}.cleaned{suffix}"
    )
    report = args.report.expanduser().resolve() if args.report else source.with_name(
        f"{source.stem}.health.md"
    )
    try:
        original = load_table(source)
        cleaned, duplicates = clean_table(original, drop_duplicates=not args.keep_duplicates)
        save_table(cleaned, output)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(make_report(source, original, cleaned, duplicates), encoding="utf-8")
    except (OSError, ValueError, ImportError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Rows: {len(original)} -> {len(cleaned)}")
    print(f"Exact duplicate rows: {duplicates}")
    print(f"Cleaned dataset: {output}")
    print(f"Markdown report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
