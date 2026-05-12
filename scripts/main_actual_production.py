# -*- coding: utf-8 -*-
"""
Main business entry for the actual production workbook.

Flow:
1. Adapt "实际生产状态表.xlsx"
2. Route groups into single-spec direct mode / multi-spec GA mode
3. Let each group choose its own best mother-board width from candidates
4. Export one consolidated workbook
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.actual_production_flow import (  # noqa: E402
    execute_actual_production_workflow,
    export_actual_production_workflow,
    summarize_workflow_run,
)
from core.config import (  # noqa: E402
    AUTO_MULTI_SPEC_DECODER_MODE,
    OUTPUT_DIR,
    PANEL_WIDTH_CANDIDATES,
)
from core.group_routing import route_adapted_groups  # noqa: E402
from core.production_state_adapter import adapt_production_state_excel  # noqa: E402


DEFAULT_INPUT = ROOT_DIR / "data" / "实际生产状态表.xlsx"
DEFAULT_OUTPUT = OUTPUT_DIR / "实际生产状态表_混合宽度结果.xlsx"
DEFAULT_ARTIFACT_DIR = OUTPUT_DIR / "actual_production_runs"
DEFAULT_PANEL_WIDTHS = ",".join(str(width) for width in PANEL_WIDTH_CANDIDATES)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按分组选择各自最优母板宽度并输出综合排版结果")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="输入 Excel 路径")
    parser.add_argument("--sheet", default=0, help="Sheet 名称或索引")
    parser.add_argument(
        "--decoder-mode",
        default=AUTO_MULTI_SPEC_DECODER_MODE,
        choices=["auto", "simple", "best_fit", "stage_based", "pattern_guided", "hybrid", "length_priority"],
        help="多规格组解码模式；auto 会按批量自动切换",
    )
    parser.add_argument(
        "--panel-widths",
        default=DEFAULT_PANEL_WIDTHS,
        help="候选母板宽度列表，逗号分隔，例如 1000,1240,1250,1500",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="输出工作簿路径")
    parser.add_argument(
        "--artifact-dir",
        default=str(DEFAULT_ARTIFACT_DIR),
        help="多规格组报告与图片输出目录",
    )
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
    return sorted(set(widths))


def build_width_usage_text(width_summary) -> str:
    if width_summary.empty:
        return "无已分配宽度"
    parts = []
    for row in width_summary.to_dict(orient="records"):
        parts.append(f"{int(row['母板宽度'])}mm: {int(row['分组数'])}组")
    return ", ".join(parts)


def print_failed_group_details(workflow_summary) -> None:
    if workflow_summary.empty or "状态" not in workflow_summary.columns:
        return

    failed_rows = workflow_summary.loc[
        workflow_summary["状态"].astype(str).str.contains("失败", na=False)
    ].copy()
    if failed_rows.empty:
        return

    print("失败组明细:")
    for row in failed_rows.to_dict(orient="records"):
        group_id = row.get("分组编号", "")
        name = row.get("品名", "")
        thickness = row.get("厚度", "")
        spec_count = row.get("规格种数", "")
        panel_width = row.get("母板宽度", "")
        order_total = row.get("订单总片数", "")
        note = str(row.get("备注", "") or "").strip()
        print(
            f"  - {group_id}: {name} 厚度 {thickness} mm, "
            f"规格种数 {spec_count}, 订单 {order_total} 件, "
            f"候选/记录母板宽度 {panel_width} mm"
        )
        if note:
            print(f"    原因: {note}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    panel_widths = parse_panel_widths(args.panel_widths)
    output_path = Path(args.output)
    artifact_root = Path(args.artifact_dir)

    adapted_data = adapt_production_state_excel(
        filepath=input_path,
        sheet_name=normalize_sheet_arg(str(args.sheet)),
    )
    routing_result = route_adapted_groups(
        adapted_data=adapted_data,
        panel_widths=panel_widths,
    )
    execution_result = execute_actual_production_workflow(
        adapted_data=adapted_data,
        routing_result=routing_result,
        decoder_mode=args.decoder_mode,
        output_dir=artifact_root,
        panel_widths=panel_widths,
        verbose=True,
    )
    export_actual_production_workflow(
        adapted_data=adapted_data,
        routing_result=routing_result,
        execution_result=execution_result,
        output_path=output_path,
    )

    summary = summarize_workflow_run(
        adapted_data=adapted_data,
        execution_result=execution_result,
        panel_width=0,
        decoder_mode=args.decoder_mode,
    )
    width_usage_text = build_width_usage_text(execution_result.width_allocation_summary)

    print("")
    print("=" * 60)
    print("实际生产状态表综合排版结果")
    print("=" * 60)
    print(f"输入文件: {input_path}")
    print(f"候选母板宽度: {', '.join(str(width) for width in panel_widths)}")
    print(f"宽度分配: {width_usage_text}")
    print(f"完成组数: {summary.completed_groups}/{summary.total_groups}")
    print(f"失败组数: {summary.failed_groups}")
    print_failed_group_details(execution_result.workflow_summary)
    print(f"订单数补切合计: {summary.total_makeup_pieces}")
    print(f"超产合计: {summary.total_overproduction_pieces}")
    print(f"总母板面积: {summary.total_panel_area:.0f}")
    print(f"总产出面积: {summary.total_output_area:.0f}")
    print(f"真实利用率: {summary.overall_efficiency:.4f}%")
    print(f"总母板消耗长度: {summary.total_consumed_length_mm:.0f} mm")
    print(f"输出工作簿: {output_path}")
    print(f"过程产物目录: {artifact_root}")


if __name__ == "__main__":
    main()
