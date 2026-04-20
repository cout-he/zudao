# -*- coding: utf-8 -*-
"""
Route adapted production groups into either:
1. 单规格直排
2. 多规格优化
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from core.config import PANEL_WIDTH, PANEL_WIDTH_CANDIDATES
from core.production_state_adapter import AdaptedProductionData


ROUTING_COLUMNS = [
    "分组编号",
    "品名",
    "厚度",
    "规格种数",
    "总片数",
    "总重量",
    "处理方式",
    "最优母板宽度",
    "最优朝向",
    "最优横向占宽",
    "最优纵向定尺",
    "每条并排数",
    "需要条数",
    "实际产出",
    "超产数",
    "总消耗长度",
    "余宽",
    "利用率(%)",
    "备注",
]

SINGLE_SPEC_PLAN_COLUMNS = [
    "分组编号",
    "品名",
    "厚度",
    "标准规格",
    "母板宽度",
    "朝向",
    "横向占宽",
    "纵向定尺",
    "每条并排数",
    "需要条数",
    "实际产出",
    "超产数",
    "总消耗长度",
    "余宽",
    "利用率(%)",
    "是否最优",
]

MULTI_SPEC_COLUMNS = [
    "分组编号",
    "品名",
    "厚度",
    "规格种数",
    "总片数",
    "总重量",
    "备注",
]


@dataclass
class GroupRoutingResult:
    routing_summary: pd.DataFrame
    single_spec_plans: pd.DataFrame
    multi_spec_groups: pd.DataFrame


def _normalize_panel_widths(panel_widths: Iterable[int] | None) -> list[int]:
    if panel_widths is None:
        panel_widths = PANEL_WIDTH_CANDIDATES or [PANEL_WIDTH]

    cleaned: set[int] = set()
    for width in panel_widths:
        int_width = int(width)
        if int_width > 0:
            cleaned.add(int_width)
    if not cleaned:
        raise ValueError("候选母板宽度不能为空")
    return sorted(cleaned)


def _build_orientation_plans(group_row: pd.Series, panel_widths: list[int]) -> list[dict]:
    short_side = float(group_row["短边"])
    long_side = float(group_row["长边"])
    demand_qty = int(group_row["片数"])
    used_area = demand_qty * short_side * long_side

    orientation_specs = [
        ("短边横放", short_side, long_side),
        ("长边横放", long_side, short_side),
    ]

    plans: list[dict] = []
    for panel_width in panel_widths:
        seen_orientations: set[tuple[float, float]] = set()
        for orientation, layout_width, layout_length in orientation_specs:
            orientation_key = (layout_width, layout_length)
            if orientation_key in seen_orientations:
                continue
            seen_orientations.add(orientation_key)

            lane_count = int(panel_width // layout_width)
            if lane_count <= 0:
                continue

            strip_count = (demand_qty + lane_count - 1) // lane_count
            actual_output = lane_count * strip_count
            over_output = actual_output - demand_qty
            total_length = strip_count * layout_length
            waste_width = panel_width - lane_count * layout_width
            total_panel_area = panel_width * total_length
            efficiency = 0.0 if total_panel_area <= 0 else 100.0 * used_area / total_panel_area

            plans.append(
                {
                    "分组编号": group_row["分组编号"],
                    "品名": group_row["品名"],
                    "厚度": group_row["厚度"],
                    "标准规格": group_row["标准规格"],
                    "母板宽度": panel_width,
                    "朝向": orientation,
                    "横向占宽": layout_width,
                    "纵向定尺": layout_length,
                    "每条并排数": lane_count,
                    "需要条数": strip_count,
                    "实际产出": actual_output,
                    "超产数": over_output,
                    "总消耗长度": total_length,
                    "余宽": waste_width,
                    "利用率(%)": efficiency,
                }
            )
    return plans


def _select_best_plan(plan_rows: list[dict]) -> dict | None:
    if not plan_rows:
        return None

    return max(
        plan_rows,
        key=lambda row: (
            round(float(row["利用率(%)"]), 8),
            -float(row["总消耗长度"]),
            -float(row["余宽"]),
            -int(row["超产数"]),
            -int(row["母板宽度"]),
        ),
    )


def route_adapted_groups(
    adapted_data: AdaptedProductionData,
    panel_widths: Iterable[int] | None = None,
) -> GroupRoutingResult:
    panel_widths = _normalize_panel_widths(panel_widths)

    detail = adapted_data.printable_detail.copy()
    grouped = adapted_data.grouped_summary.copy()

    routing_rows: list[dict] = []
    all_single_spec_plans: list[dict] = []

    for group_row in grouped.to_dict(orient="records"):
        base_row = {
            "分组编号": group_row["分组编号"],
            "品名": group_row["品名"],
            "厚度": group_row["厚度"],
            "规格种数": group_row["规格种数"],
            "总片数": group_row["总片数"],
            "总重量": group_row["总重量"],
        }

        if int(group_row["规格种数"]) <= 1:
            group_detail = detail.loc[detail["分组编号"] == group_row["分组编号"]]
            if group_detail.empty:
                routing_rows.append(
                    {
                        **base_row,
                        "处理方式": "单规格直排",
                        "最优母板宽度": None,
                        "最优朝向": "",
                        "最优横向占宽": None,
                        "最优纵向定尺": None,
                        "每条并排数": None,
                        "需要条数": None,
                        "实际产出": None,
                        "超产数": None,
                        "总消耗长度": None,
                        "余宽": None,
                        "利用率(%)": None,
                        "备注": "分组缺少可排版明细",
                    }
                )
                continue

            group_spec_row = group_detail.iloc[0]
            plan_rows = _build_orientation_plans(group_spec_row, panel_widths)
            best_plan = _select_best_plan(plan_rows)

            best_key = None
            if best_plan is not None:
                best_key = (
                    best_plan["母板宽度"],
                    best_plan["朝向"],
                    best_plan["横向占宽"],
                    best_plan["纵向定尺"],
                )

            for row in plan_rows:
                row["是否最优"] = "是" if (
                    row["母板宽度"],
                    row["朝向"],
                    row["横向占宽"],
                    row["纵向定尺"],
                ) == best_key else ""
                all_single_spec_plans.append(row)

            if best_plan is None:
                routing_rows.append(
                    {
                        **base_row,
                        "处理方式": "多规格优化",
                        "最优母板宽度": None,
                        "最优朝向": "",
                        "最优横向占宽": None,
                        "最优纵向定尺": None,
                        "每条并排数": None,
                        "需要条数": None,
                        "实际产出": None,
                        "超产数": None,
                        "总消耗长度": None,
                        "余宽": None,
                        "利用率(%)": None,
                        "备注": "单规格在所有候选母板宽度下都无法直排，转入 GA 兜底",
                    }
                )
            else:
                routing_rows.append(
                    {
                        **base_row,
                        "处理方式": "单规格直排",
                        "最优母板宽度": best_plan["母板宽度"],
                        "最优朝向": best_plan["朝向"],
                        "最优横向占宽": best_plan["横向占宽"],
                        "最优纵向定尺": best_plan["纵向定尺"],
                        "每条并排数": best_plan["每条并排数"],
                        "需要条数": best_plan["需要条数"],
                        "实际产出": best_plan["实际产出"],
                        "超产数": best_plan["超产数"],
                        "总消耗长度": best_plan["总消耗长度"],
                        "余宽": best_plan["余宽"],
                        "利用率(%)": best_plan["利用率(%)"],
                        "备注": f"已比较 {len(plan_rows)} 个直排候选方案",
                    }
                )
        else:
            routing_rows.append(
                {
                    **base_row,
                    "处理方式": "多规格优化",
                    "最优母板宽度": None,
                    "最优朝向": "",
                    "最优横向占宽": None,
                    "最优纵向定尺": None,
                    "每条并排数": None,
                    "需要条数": None,
                    "实际产出": None,
                    "超产数": None,
                    "总消耗长度": None,
                    "余宽": None,
                    "利用率(%)": None,
                    "备注": "规格种数大于等于 2，保留给后续混排优化",
                }
            )

    routing_summary = pd.DataFrame(routing_rows)
    if routing_summary.empty:
        routing_summary = pd.DataFrame(columns=ROUTING_COLUMNS)
    else:
        routing_summary = routing_summary.loc[:, ROUTING_COLUMNS]

    single_spec_plans = pd.DataFrame(all_single_spec_plans)
    if single_spec_plans.empty:
        single_spec_plans = pd.DataFrame(columns=SINGLE_SPEC_PLAN_COLUMNS)
    else:
        single_spec_plans = single_spec_plans.loc[:, SINGLE_SPEC_PLAN_COLUMNS]
        single_spec_plans = single_spec_plans.sort_values(
            ["分组编号", "母板宽度", "朝向"],
            ignore_index=True,
        )

    multi_spec_groups = routing_summary.loc[
        routing_summary["处理方式"] == "多规格优化",
        MULTI_SPEC_COLUMNS,
    ].copy()
    if multi_spec_groups.empty:
        multi_spec_groups = pd.DataFrame(columns=MULTI_SPEC_COLUMNS)
    else:
        multi_spec_groups = multi_spec_groups.sort_values(["分组编号"], ignore_index=True)

    return GroupRoutingResult(
        routing_summary=routing_summary,
        single_spec_plans=single_spec_plans,
        multi_spec_groups=multi_spec_groups,
    )


def export_group_routing_workbook(
    adapted_data: AdaptedProductionData,
    routing_result: GroupRoutingResult,
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        adapted_data.printable_detail.to_excel(writer, sheet_name="可排版明细", index=False)
        adapted_data.excluded_detail.to_excel(writer, sheet_name="剔除明细", index=False)
        adapted_data.grouped_summary.to_excel(writer, sheet_name="按品名厚度分组结果", index=False)
        routing_result.routing_summary.to_excel(writer, sheet_name="分组处理策略", index=False)
        routing_result.single_spec_plans.to_excel(writer, sheet_name="单规格直排候选方案", index=False)
        routing_result.multi_spec_groups.to_excel(writer, sheet_name="GA待优化分组", index=False)

    return output_path
