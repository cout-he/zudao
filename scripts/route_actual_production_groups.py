# -*- coding: utf-8 -*-
"""
Build routing decisions for adapted production groups.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.group_routing import (  # noqa: E402
    export_group_routing_workbook,
    route_adapted_groups,
)
from core.config import PANEL_WIDTH_CANDIDATES  # noqa: E402
from core.production_state_adapter import adapt_production_state_excel  # noqa: E402


DEFAULT_INPUT = ROOT_DIR / "data" / "实际生产状态表.xlsx"
DEFAULT_OUTPUT = ROOT_DIR / "outputs" / "实际生产状态表_分组处理方案.xlsx"
DEFAULT_PANEL_WIDTHS = ",".join(str(width) for width in PANEL_WIDTH_CANDIDATES)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="为实际生产状态表生成分组处理策略")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="输入 Excel 路径")
    parser.add_argument("--sheet", default=0, help="Sheet 名称或序号，默认第一个 sheet")
    parser.add_argument(
        "--panel-widths",
        default=DEFAULT_PANEL_WIDTHS,
        help="候选母板宽度，使用逗号分隔，例如 1000,1200,1240,1250,1500",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="输出 Excel 路径")
    return parser


def normalize_sheet_arg(sheet_arg: str) -> str | int:
    try:
        return int(sheet_arg)
    except ValueError:
        return sheet_arg


def parse_panel_widths(raw_text: str) -> list[int]:
    widths = []
    for chunk in str(raw_text).split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        widths.append(int(float(chunk)))
    if not widths:
        raise ValueError("候选母板宽度不能为空")
    return widths


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
    routing_result = route_adapted_groups(
        adapted_data=adapted_data,
        panel_widths=parse_panel_widths(args.panel_widths),
    )
    output_path = export_group_routing_workbook(
        adapted_data=adapted_data,
        routing_result=routing_result,
        output_path=args.output,
    )

    single_spec_count = int((routing_result.routing_summary["处理方式"] == "单规格直排").sum())
    ga_count = int((routing_result.routing_summary["处理方式"] == "多规格优化").sum())

    print(f"输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    print(f"单规格直排分组: {single_spec_count} 组")
    print(f"GA待优化分组: {ga_count} 组")
    print(f"单规格直排候选方案: {len(routing_result.single_spec_plans)} 条")


if __name__ == "__main__":
    main()
