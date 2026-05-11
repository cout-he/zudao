# -*- coding: utf-8 -*-
"""Run standalone baseline experiments on selected locked-width groups."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from baseline_methods.common import (  # noqa: E402
    DEFAULT_FINAL_WORKBOOK,
    DEFAULT_INPUT_WORKBOOK,
    DEFAULT_OUTPUT_DIR,
    ensure_dir,
    load_group_cases,
    write_group_report,
)
from baseline_methods.pattern_generation import solve as solve_pattern_generation  # noqa: E402
from baseline_methods.two_stage_greedy import solve as solve_two_stage_greedy  # noqa: E402


DEFAULT_GROUPS = "G001,G006,G020,G036"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="锁定母板宽度的 baseline 对比实验")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_WORKBOOK), help="原始实际生产状态表")
    parser.add_argument("--final-workbook", default=str(DEFAULT_FINAL_WORKBOOK), help="现有最终主结果")
    parser.add_argument("--groups", default=DEFAULT_GROUPS, help="实验分组编号，逗号分隔")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="实验输出目录")
    return parser.parse_args()


def build_summary_rows(case, baseline_results):
    rows = [
        {
            "分组编号": case.group_id,
            "方法": "现有方法",
            "方法细节": f"{case.ours_method} / {case.ours_decoder}",
            "锁定母板宽度": case.panel_width,
            "规格数": len(case.specs),
            "订单数": case.ours_order_total,
            "算法产出数": case.ours_output_total,
            "补切数": case.ours_makeup_total,
            "超产数": case.ours_over_total,
            "总消耗长度(mm)": int(round(case.ours_consumed_length_mm)),
            "真实利用率(%)": case.ours_utilization_pct,
            "运行耗时(s)": None,
            "阶段数": None,
        }
    ]

    for result in baseline_results:
        rows.append(
            {
                "分组编号": case.group_id,
                "方法": result.method_name,
                "方法细节": result.method_key,
                "锁定母板宽度": result.panel_width,
                "规格数": len(case.specs),
                "订单数": result.order_total,
                "算法产出数": result.produced_total,
                "补切数": result.makeup_total,
                "超产数": result.over_total,
                "总消耗长度(mm)": result.consumed_length_mm,
                "真实利用率(%)": result.utilization_pct,
                "运行耗时(s)": result.runtime_seconds,
                "阶段数": result.stage_count,
            }
        )
    return rows


def build_spec_rows(case):
    return [
        {
            "分组编号": case.group_id,
            "品名": case.product_name,
            "厚度": case.thickness,
            "锁定母板宽度": case.panel_width,
            "标准规格": spec.standard_spec,
            "宽(mm)": spec.width,
            "长(mm)": spec.length,
            "需求数量": spec.demand_qty,
        }
        for spec in case.specs
    ]


def build_stage_rows(case, result):
    rows = []
    for stage in result.stage_plans:
        rows.append(
            {
                "分组编号": case.group_id,
                "方法": result.method_name,
                "阶段": stage.stage_index,
                "重复次数": stage.repeat_count,
                "阶段长度(mm)": stage.stage_length,
                "占宽(mm)": stage.used_width,
                "余宽(mm)": stage.waste_width,
                "刀道分配": "; ".join(
                    f"{spec_key} x {lane_count}"
                    for spec_key, lane_count in sorted(stage.lane_counts.items())
                    if lane_count > 0
                ),
                "单次产出": "; ".join(
                    f"{spec_key}: {qty}"
                    for spec_key, qty in sorted(stage.produced_per_repeat.items())
                    if qty > 0
                ),
                "总产出": "; ".join(
                    f"{spec_key}: {qty}"
                    for spec_key, qty in sorted(stage.produced_total.items())
                    if qty > 0
                ),
            }
        )
    return rows


def build_markdown_summary(cases, grouped_results) -> str:
    lines = [
        "# 锁定母板宽度 Baseline 对比实验",
        "",
        "实验约束：",
        "- 不改动现有主流程代码，只在独立目录实现 baseline。",
        "- 每个分组直接读取现有最终结果里的已选母板宽度，保证实验变量一致。",
        f"- 本次实验分组：{', '.join(case.group_id for case in cases)}。",
        "",
    ]

    for case in cases:
        results = grouped_results[case.group_id]
        lines.append(f"## {case.group_id}")
        lines.append("")
        lines.append(
            f"锁定宽度 `{case.panel_width}` mm，现有方法 `{case.ours_method} / {case.ours_decoder}`。"
        )
        lines.append("")
        lines.append("| 方法 | 订单数 | 产出数 | 补切数 | 超产数 | 消耗长度(mm) | 真实利用率(%) | 耗时(s) |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        lines.append(
            f"| 现有方法 | {case.ours_order_total} | {case.ours_output_total} | "
            f"{case.ours_makeup_total} | {case.ours_over_total} | "
            f"{int(round(case.ours_consumed_length_mm))} | {case.ours_utilization_pct:.4f} | - |"
        )
        for result in results:
            lines.append(
                f"| {result.method_name} | {result.order_total} | {result.produced_total} | "
                f"{result.makeup_total} | {result.over_total} | {result.consumed_length_mm} | "
                f"{result.utilization_pct:.4f} | {result.runtime_seconds:.4f} |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    group_ids = [chunk.strip() for chunk in str(args.groups).split(",") if chunk.strip()]
    output_dir = ensure_dir(Path(args.output_dir))
    reports_dir = ensure_dir(output_dir / "group_reports")

    cases = load_group_cases(
        input_workbook=Path(args.input),
        final_workbook=Path(args.final_workbook),
        target_groups=group_ids,
    )

    summary_rows = []
    spec_rows = []
    stage_rows = []
    grouped_results = {}

    for case in cases:
        greedy_result = solve_two_stage_greedy(case)
        pattern_result = solve_pattern_generation(case)
        grouped_results[case.group_id] = [greedy_result, pattern_result]

        summary_rows.extend(build_summary_rows(case, [greedy_result, pattern_result]))
        spec_rows.extend(build_spec_rows(case))
        stage_rows.extend(build_stage_rows(case, greedy_result))
        stage_rows.extend(build_stage_rows(case, pattern_result))

        write_group_report(
            case,
            greedy_result,
            reports_dir / f"{case.group_id}_two_stage_greedy_report.txt",
        )
        write_group_report(
            case,
            pattern_result,
            reports_dir / f"{case.group_id}_pattern_generation_report.txt",
        )

    summary_df = pd.DataFrame(summary_rows)
    spec_df = pd.DataFrame(spec_rows)
    stage_df = pd.DataFrame(stage_rows)

    summary_path = output_dir / "locked_width_baseline_summary.xlsx"
    with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="对比汇总", index=False)
        spec_df.to_excel(writer, sheet_name="实验分组规格", index=False)
        stage_df.to_excel(writer, sheet_name="阶段明细", index=False)

    markdown_path = output_dir / "README.md"
    markdown_path.write_text(build_markdown_summary(cases, grouped_results), encoding="utf-8")

    print(f"已输出 baseline 实验目录: {output_dir}")
    print(f"汇总文件: {summary_path}")


if __name__ == "__main__":
    main()

