# -*- coding: utf-8 -*-
"""
Input adapter for the client's "实际生产状态表" workbook.

This module is intentionally isolated from the GA solver so we can first
standardize the business data before deciding how to feed it into the
placement algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


RAW_COLUMNS = ["品名", "规格", "片数", "重量"]
DETAIL_COLUMNS = [
    "分组编号",
    "品名",
    "厚度",
    "尺寸1",
    "尺寸2",
    "短边",
    "长边",
    "标准规格",
    "片数",
    "重量",
    "合并行数",
]
EXCLUDED_COLUMNS = [
    "原始行号",
    "品名",
    "规格",
    "片数",
    "重量",
    "剔除原因",
]
GROUP_COLUMNS = [
    "分组编号",
    "品名",
    "厚度",
    "规格种数",
    "总片数",
    "总重量",
]

COIL_MARKER = "卷料"
SPECIAL_SPEC_MARKERS = ("±", "+", "/", "(", ")", "（", "）", "[", "]", "【", "】")


@dataclass
class AdaptedProductionData:
    printable_detail: pd.DataFrame
    excluded_detail: pd.DataFrame
    grouped_summary: pd.DataFrame


def _clean_numeric_text(value: str) -> str:
    text = str(value).strip()
    text = text.replace(" ", "")
    text = text.replace("mm", "")
    text = text.replace("MM", "")
    text = text.replace("×", "*")
    text = text.replace("X", "*")
    text = text.replace("x", "*")
    return text


def _is_coil_spec(spec_text: str) -> bool:
    return COIL_MARKER in spec_text


def _has_special_spec_marker(spec_text: str) -> bool:
    return any(marker in spec_text for marker in SPECIAL_SPEC_MARKERS)


def _parse_board_spec(spec_text: str) -> tuple[float, float, float] | None:
    cleaned = _clean_numeric_text(spec_text)
    if cleaned.count("*") != 2:
        return None

    parts = cleaned.split("*")
    if len(parts) != 3:
        return None

    try:
        thickness, size_1, size_2 = (float(part) for part in parts)
    except ValueError:
        return None
    return thickness, size_1, size_2


def _format_number(value: float) -> str:
    if pd.isna(value):
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{float(value):g}"


def _build_standard_spec(thickness: float, short_side: float, long_side: float) -> str:
    return "*".join(
        [
            _format_number(thickness),
            _format_number(short_side),
            _format_number(long_side),
        ]
    )


def _load_raw_table(filepath: str | Path, sheet_name: str | int = 0) -> pd.DataFrame:
    table = pd.read_excel(filepath, sheet_name=sheet_name)
    if list(table.columns[:4]) != RAW_COLUMNS:
        table = table.rename(
            columns={
                table.columns[0]: RAW_COLUMNS[0],
                table.columns[1]: RAW_COLUMNS[1],
                table.columns[2]: RAW_COLUMNS[2],
                table.columns[3]: RAW_COLUMNS[3],
            }
        )

    missing = [column for column in RAW_COLUMNS if column not in table.columns]
    if missing:
        raise ValueError(f"输入表缺少必要列: {missing}")

    table = table.loc[:, RAW_COLUMNS].copy()
    table["原始行号"] = table.index + 2
    table["品名"] = table["品名"].astype(str).str.strip()
    table["规格"] = table["规格"].astype(str).str.strip()
    table["片数"] = pd.to_numeric(table["片数"], errors="coerce")
    table["重量"] = pd.to_numeric(table["重量"], errors="coerce")
    return table


def _classify_rows(raw_table: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    printable_rows: list[dict] = []
    excluded_rows: list[dict] = []

    for row in raw_table.to_dict(orient="records"):
        spec_text = str(row["规格"]).strip()

        if not spec_text or spec_text.lower() == "nan":
            excluded_rows.append(
                {
                    "原始行号": row["原始行号"],
                    "品名": row["品名"],
                    "规格": row["规格"],
                    "片数": row["片数"],
                    "重量": row["重量"],
                    "剔除原因": "空规格",
                }
            )
            continue

        if _is_coil_spec(spec_text):
            excluded_rows.append(
                {
                    "原始行号": row["原始行号"],
                    "品名": row["品名"],
                    "规格": row["规格"],
                    "片数": row["片数"],
                    "重量": row["重量"],
                    "剔除原因": "卷料",
                }
            )
            continue

        if _has_special_spec_marker(spec_text):
            excluded_rows.append(
                {
                    "原始行号": row["原始行号"],
                    "品名": row["品名"],
                    "规格": row["规格"],
                    "片数": row["片数"],
                    "重量": row["重量"],
                    "剔除原因": "特殊规格写法",
                }
            )
            continue

        parsed = _parse_board_spec(spec_text)
        if parsed is None:
            excluded_rows.append(
                {
                    "原始行号": row["原始行号"],
                    "品名": row["品名"],
                    "规格": row["规格"],
                    "片数": row["片数"],
                    "重量": row["重量"],
                    "剔除原因": "规格无法解析为三段板材",
                }
            )
            continue

        thickness, size_1, size_2 = parsed
        short_side = min(size_1, size_2)
        long_side = max(size_1, size_2)
        printable_rows.append(
            {
                "品名": row["品名"],
                "厚度": thickness,
                "尺寸1": size_1,
                "尺寸2": size_2,
                "短边": short_side,
                "长边": long_side,
                "标准规格": _build_standard_spec(thickness, short_side, long_side),
                "片数": row["片数"],
                "重量": row["重量"],
                "原始行号": row["原始行号"],
            }
        )

    return printable_rows, excluded_rows


def _make_detail_table(printable_rows: Iterable[dict]) -> pd.DataFrame:
    detail = pd.DataFrame(printable_rows)
    if detail.empty:
        return pd.DataFrame(columns=DETAIL_COLUMNS)

    grouped = (
        detail.groupby(
            ["品名", "厚度", "短边", "长边", "标准规格"],
            dropna=False,
            as_index=False,
        )
        .agg(
            片数=("片数", "sum"),
            重量=("重量", "sum"),
            合并行数=("原始行号", "size"),
        )
        .sort_values(["品名", "厚度", "短边", "长边"], ignore_index=True)
    )

    grouped["尺寸1"] = grouped["短边"]
    grouped["尺寸2"] = grouped["长边"]

    grouped["分组编号"] = (
        grouped.groupby(["品名", "厚度"], sort=False).ngroup() + 1
    ).map(lambda index: f"G{index:03d}")

    return grouped.loc[:, DETAIL_COLUMNS]


def _make_group_table(detail_table: pd.DataFrame) -> pd.DataFrame:
    if detail_table.empty:
        return pd.DataFrame(columns=GROUP_COLUMNS)

    group_table = (
        detail_table.groupby(["分组编号", "品名", "厚度"], as_index=False)
        .agg(
            规格种数=("标准规格", "nunique"),
            总片数=("片数", "sum"),
            总重量=("重量", "sum"),
        )
        .sort_values(["分组编号"], ignore_index=True)
    )
    return group_table.loc[:, GROUP_COLUMNS]


def _make_excluded_table(excluded_rows: Iterable[dict]) -> pd.DataFrame:
    excluded = pd.DataFrame(excluded_rows)
    if excluded.empty:
        return pd.DataFrame(columns=EXCLUDED_COLUMNS)
    return excluded.loc[:, EXCLUDED_COLUMNS].sort_values(
        ["剔除原因", "品名", "原始行号"], ignore_index=True
    )


def adapt_production_state_excel(
    filepath: str | Path,
    sheet_name: str | int = 0,
) -> AdaptedProductionData:
    raw_table = _load_raw_table(filepath=filepath, sheet_name=sheet_name)
    printable_rows, excluded_rows = _classify_rows(raw_table)
    printable_detail = _make_detail_table(printable_rows)
    excluded_detail = _make_excluded_table(excluded_rows)
    grouped_summary = _make_group_table(printable_detail)
    return AdaptedProductionData(
        printable_detail=printable_detail,
        excluded_detail=excluded_detail,
        grouped_summary=grouped_summary,
    )


def export_adapted_workbook(
    adapted_data: AdaptedProductionData,
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        adapted_data.printable_detail.to_excel(
            writer,
            sheet_name="可排版明细",
            index=False,
        )
        adapted_data.excluded_detail.to_excel(
            writer,
            sheet_name="剔除明细",
            index=False,
        )
        adapted_data.grouped_summary.to_excel(
            writer,
            sheet_name="按品名厚度分组结果",
            index=False,
        )

    return output_path
