# -*- coding: utf-8 -*-
"""Common helpers for standalone baseline experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Iterable

import pandas as pd

from core.production_state_adapter import adapt_production_state_excel


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_WORKBOOK = ROOT_DIR / "data" / "实际生产状态表.xlsx"
DEFAULT_FINAL_WORKBOOK = ROOT_DIR / "outputs" / "实际生产状态表_四宽度混合核对.xlsx"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "outputs" / "baseline_locked_width_compare"


@dataclass(frozen=True)
class SpecDemand:
    group_id: str
    product_name: str
    thickness: float
    standard_spec: str
    width: int
    length: int
    demand_qty: int
    weight: float

    @property
    def area_per_piece(self) -> int:
        return self.width * self.length


@dataclass
class GroupCase:
    group_id: str
    product_name: str
    thickness: float
    panel_width: int
    specs: list[SpecDemand]
    ours_method: str
    ours_decoder: str
    ours_order_total: int
    ours_output_total: int
    ours_makeup_total: int
    ours_over_total: int
    ours_consumed_length_mm: float
    ours_utilization_pct: float

    @property
    def total_demand_area(self) -> int:
        return sum(spec.demand_qty * spec.area_per_piece for spec in self.specs)


@dataclass
class StagePlan:
    stage_index: int
    repeat_count: int
    stage_length: int
    lane_counts: dict[str, int]
    produced_per_repeat: dict[str, int]
    produced_total: dict[str, int]
    used_width: int
    waste_width: int


@dataclass
class BaselineResult:
    method_key: str
    method_name: str
    group_id: str
    panel_width: int
    runtime_seconds: float
    order_total: int
    produced_total: int
    makeup_total: int
    over_total: int
    consumed_length_mm: int
    panel_area: int
    produced_area: int
    order_area: int
    utilization_pct: float
    stage_count: int
    stage_plans: list[StagePlan]
    demand_by_spec: dict[str, int]
    produced_by_spec: dict[str, int]


def timed_call(fn, *args, **kwargs):
    started = perf_counter()
    result = fn(*args, **kwargs)
    ended = perf_counter()
    return result, ended - started


def load_group_cases(
    input_workbook: Path = DEFAULT_INPUT_WORKBOOK,
    final_workbook: Path = DEFAULT_FINAL_WORKBOOK,
    target_groups: Iterable[str] | None = None,
) -> list[GroupCase]:
    adapted = adapt_production_state_excel(input_workbook)
    detail = adapted.printable_detail.copy()
    workflow = pd.read_excel(final_workbook, sheet_name="主流程汇总")

    if target_groups is None:
        target_groups = ["G001", "G006", "G020", "G036"]
    target_set = {str(group_id).strip() for group_id in target_groups}

    workflow = workflow.loc[workflow["分组编号"].isin(target_set)].copy()
    detail = detail.loc[detail["分组编号"].isin(target_set)].copy()

    cases: list[GroupCase] = []
    for row in workflow.sort_values("分组编号").to_dict(orient="records"):
        group_id = str(row["分组编号"]).strip()
        group_specs = detail.loc[detail["分组编号"] == group_id].sort_values(
            ["短边", "长边", "标准规格"]
        )
        specs = [
            SpecDemand(
                group_id=group_id,
                product_name=str(spec_row["品名"]).strip(),
                thickness=float(spec_row["厚度"]),
                standard_spec=str(spec_row["标准规格"]).strip(),
                width=int(round(float(spec_row["短边"]))),
                length=int(round(float(spec_row["长边"]))),
                demand_qty=int(round(float(spec_row["片数"]))),
                weight=float(spec_row["重量"]),
            )
            for spec_row in group_specs.to_dict(orient="records")
        ]
        if not specs:
            continue

        cases.append(
            GroupCase(
                group_id=group_id,
                product_name=str(row["品名"]).strip(),
                thickness=float(row["厚度"]),
                panel_width=int(round(float(row["母板宽度"]))),
                specs=specs,
                ours_method=str(row["处理方式"]).strip(),
                ours_decoder=str(row["解码方式"]).strip(),
                ours_order_total=int(round(float(row["订单总片数"]))),
                ours_output_total=int(round(float(row["算法产出总片数"]))),
                ours_makeup_total=int(round(float(row["补切数"]))),
                ours_over_total=int(round(float(row["超产数"]))),
                ours_consumed_length_mm=float(row["总消耗长度(mm)"]),
                ours_utilization_pct=float(row["真实利用率(%)"]),
            )
        )
    return cases


def build_result_from_stage_plans(
    *,
    method_key: str,
    method_name: str,
    case: GroupCase,
    runtime_seconds: float,
    stage_plans: list[StagePlan],
) -> BaselineResult:
    demand_by_spec = {spec.standard_spec: spec.demand_qty for spec in case.specs}
    area_by_spec = {spec.standard_spec: spec.area_per_piece for spec in case.specs}
    produced_by_spec = {spec.standard_spec: 0 for spec in case.specs}

    for stage in stage_plans:
        for spec_key, produced in stage.produced_total.items():
            produced_by_spec[spec_key] += int(produced)

    order_total = sum(demand_by_spec.values())
    produced_total = sum(produced_by_spec.values())
    makeup_total = sum(
        max(0, demand_by_spec[spec_key] - produced_by_spec.get(spec_key, 0))
        for spec_key in demand_by_spec
    )
    over_total = sum(
        max(0, produced_by_spec.get(spec_key, 0) - demand_by_spec[spec_key])
        for spec_key in demand_by_spec
    )
    consumed_length_mm = sum(stage.stage_length * stage.repeat_count for stage in stage_plans)
    panel_area = int(case.panel_width * consumed_length_mm)
    produced_area = sum(
        produced_by_spec[spec_key] * area_by_spec[spec_key] for spec_key in produced_by_spec
    )
    order_area = sum(
        demand_by_spec[spec_key] * area_by_spec[spec_key] for spec_key in demand_by_spec
    )
    utilization_pct = 0.0 if panel_area <= 0 else 100.0 * produced_area / panel_area

    return BaselineResult(
        method_key=method_key,
        method_name=method_name,
        group_id=case.group_id,
        panel_width=case.panel_width,
        runtime_seconds=runtime_seconds,
        order_total=order_total,
        produced_total=produced_total,
        makeup_total=makeup_total,
        over_total=over_total,
        consumed_length_mm=consumed_length_mm,
        panel_area=panel_area,
        produced_area=produced_area,
        order_area=order_area,
        utilization_pct=utilization_pct,
        stage_count=len(stage_plans),
        stage_plans=stage_plans,
        demand_by_spec=demand_by_spec,
        produced_by_spec=produced_by_spec,
    )


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_stage_lines(result: BaselineResult) -> list[str]:
    lines: list[str] = []
    for stage in result.stage_plans:
        lane_text = ", ".join(
            f"{spec_key} x {lane_count}"
            for spec_key, lane_count in sorted(stage.lane_counts.items())
            if lane_count > 0
        )
        produced_text = ", ".join(
            f"{spec_key}: {qty}"
            for spec_key, qty in sorted(stage.produced_total.items())
            if qty > 0
        )
        lines.append(
            "阶段 "
            f"{stage.stage_index}: 长度 {stage.stage_length} mm, 重复 {stage.repeat_count} 次, "
            f"占宽 {stage.used_width}/{result.panel_width}, 余宽 {stage.waste_width}, "
            f"刀道 {lane_text or '-'}, 产出 {produced_text or '-'}"
        )
    return lines


def write_group_report(case: GroupCase, result: BaselineResult, output_path: Path) -> None:
    lines = [
        f"分组编号: {case.group_id}",
        f"品名 / 厚度: {case.product_name} / {case.thickness:g}",
        f"固定母板宽度: {case.panel_width} mm",
        f"Baseline 方法: {result.method_name}",
        f"运行耗时: {result.runtime_seconds:.4f} s",
        "",
        "规格明细:",
    ]
    for spec in case.specs:
        lines.append(
            f"- {spec.standard_spec}: 宽 {spec.width} mm, 长 {spec.length} mm, 需求 {spec.demand_qty} 件"
        )

    lines.extend(
        [
            "",
            "结果汇总:",
            f"- 订单数: {result.order_total}",
            f"- 算法产出数: {result.produced_total}",
            f"- 补切数: {result.makeup_total}",
            f"- 超产数: {result.over_total}",
            f"- 总消耗长度: {result.consumed_length_mm} mm",
            f"- 真实利用率: {result.utilization_pct:.4f}%",
            f"- 阶段数: {result.stage_count}",
            "",
            "阶段计划:",
        ]
    )
    lines.extend(format_stage_lines(result) or ["- 无可用阶段计划"])

    lines.extend(
        [
            "",
            "和现有方法对照:",
            f"- 现有方法: {case.ours_method} / {case.ours_decoder}",
            f"- 现有产出数: {case.ours_output_total}",
            f"- 现有补切数: {case.ours_makeup_total}",
            f"- 现有超产数: {case.ours_over_total}",
            f"- 现有总消耗长度: {case.ours_consumed_length_mm:.0f} mm",
            f"- 现有真实利用率: {case.ours_utilization_pct:.4f}%",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")

