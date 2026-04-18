# -*- coding: utf-8 -*-
"""
Prepare the client's actual production workbook into three standardized sheets:
1. 可排版明细
2. 剔除明细
3. 按品名厚度分组结果
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.production_state_adapter import (  # noqa: E402
    adapt_production_state_excel,
    export_adapted_workbook,
)


DEFAULT_INPUT = ROOT_DIR / "data" / "实际生产状态表.xlsx"
DEFAULT_OUTPUT = ROOT_DIR / "outputs" / "实际生产状态表_适配结果.xlsx"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="适配实际生产状态表并导出标准化结果")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="输入 Excel 路径",
    )
    parser.add_argument(
        "--sheet",
        default=0,
        help="Sheet 名称或序号，默认第一个 sheet",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="输出 Excel 路径",
    )
    return parser


def normalize_sheet_arg(sheet_arg: str) -> str | int:
    try:
        return int(sheet_arg)
    except ValueError:
        return sheet_arg


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    adapted_data = adapt_production_state_excel(
        filepath=input_path,
        sheet_name=normalize_sheet_arg(str(args.sheet)),
    )
    output_path = export_adapted_workbook(adapted_data, args.output)

    print(f"输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    print(f"可排版明细: {len(adapted_data.printable_detail)} 行")
    print(f"剔除明细: {len(adapted_data.excluded_detail)} 行")
    print(f"按品名厚度分组结果: {len(adapted_data.grouped_summary)} 组")


if __name__ == "__main__":
    main()
