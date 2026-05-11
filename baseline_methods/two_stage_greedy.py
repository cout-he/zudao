# -*- coding: utf-8 -*-
"""Industrial-style two-stage guillotine greedy baseline."""

from __future__ import annotations

import math

from baseline_methods.common import (
    BaselineResult,
    GroupCase,
    StagePlan,
    build_result_from_stage_plans,
    timed_call,
)


OVER_AREA_PENALTY = 0.35
WASTE_WIDTH_PENALTY = 0.05


def _build_greedy_pattern(case: GroupCase, remaining: dict[str, int], stage_length: int):
    lane_counts = {spec.standard_spec: 0 for spec in case.specs}
    used_width = 0

    while True:
        best_spec = None
        best_score = None

        for spec in case.specs:
            pieces_per_lane = stage_length // spec.length
            if pieces_per_lane <= 0:
                continue
            if used_width + spec.width > case.panel_width:
                continue

            current_lanes = lane_counts[spec.standard_spec]
            lane_limit = max(1, math.ceil(remaining[spec.standard_spec] / pieces_per_lane))
            if current_lanes >= lane_limit:
                continue

            useful_pieces = min(remaining[spec.standard_spec], pieces_per_lane)
            over_pieces = max(0, pieces_per_lane - remaining[spec.standard_spec])
            effective_area = useful_pieces * spec.area_per_piece
            over_area = over_pieces * spec.area_per_piece
            score = (
                (effective_area - OVER_AREA_PENALTY * over_area) / spec.width,
                useful_pieces,
                spec.width,
                -spec.length,
            )
            if best_score is None or score > best_score:
                best_score = score
                best_spec = spec

        if best_spec is None:
            break

        lane_counts[best_spec.standard_spec] += 1
        used_width += best_spec.width

    if used_width <= 0:
        return None

    produced_per_repeat = {}
    for spec in case.specs:
        pieces_per_lane = stage_length // spec.length
        produced_per_repeat[spec.standard_spec] = lane_counts[spec.standard_spec] * pieces_per_lane

    waste_width = case.panel_width - used_width
    useful_area = 0
    over_area = 0
    for spec in case.specs:
        produced = produced_per_repeat[spec.standard_spec]
        useful_area += min(remaining[spec.standard_spec], produced) * spec.area_per_piece
        over_area += max(0, produced - remaining[spec.standard_spec]) * spec.area_per_piece

    stage_area = case.panel_width * stage_length
    normalized_score = 0.0
    if stage_area > 0:
        normalized_score = (
            useful_area
            - OVER_AREA_PENALTY * over_area
            - WASTE_WIDTH_PENALTY * waste_width * stage_length
        ) / stage_area

    return {
        "stage_length": stage_length,
        "lane_counts": lane_counts,
        "produced_per_repeat": produced_per_repeat,
        "used_width": used_width,
        "waste_width": waste_width,
        "normalized_score": normalized_score,
    }


def _select_best_stage(case: GroupCase, remaining: dict[str, int]):
    best_pattern = None
    for stage_length in sorted({spec.length for spec in case.specs}):
        pattern = _build_greedy_pattern(case, remaining, stage_length)
        if pattern is None:
            continue
        if best_pattern is None or pattern["normalized_score"] > best_pattern["normalized_score"]:
            best_pattern = pattern
    return best_pattern


def _safe_repeat_count(remaining: dict[str, int], produced_per_repeat: dict[str, int]) -> int:
    positive_limits = []
    for spec_key, produced in produced_per_repeat.items():
        if produced <= 0:
            continue
        remaining_qty = remaining[spec_key]
        if remaining_qty >= produced:
            positive_limits.append(max(1, remaining_qty // produced))
    if not positive_limits:
        return 1
    return max(1, min(positive_limits))


def solve(case: GroupCase) -> BaselineResult:
    def _run() -> BaselineResult:
        remaining = {spec.standard_spec: spec.demand_qty for spec in case.specs}
        stage_plans: list[StagePlan] = []
        max_iterations = 1000

        for iteration in range(max_iterations):
            if all(value <= 0 for value in remaining.values()):
                break

            pattern = _select_best_stage(case, remaining)
            if pattern is None:
                break

            repeat_count = _safe_repeat_count(remaining, pattern["produced_per_repeat"])
            produced_total = {
                spec_key: qty * repeat_count
                for spec_key, qty in pattern["produced_per_repeat"].items()
            }
            for spec_key, produced in produced_total.items():
                remaining[spec_key] -= produced

            stage_plans.append(
                StagePlan(
                    stage_index=iteration + 1,
                    repeat_count=repeat_count,
                    stage_length=int(pattern["stage_length"]),
                    lane_counts={
                        spec_key: int(lane_count)
                        for spec_key, lane_count in pattern["lane_counts"].items()
                    },
                    produced_per_repeat={
                        spec_key: int(qty)
                        for spec_key, qty in pattern["produced_per_repeat"].items()
                    },
                    produced_total={spec_key: int(qty) for spec_key, qty in produced_total.items()},
                    used_width=int(pattern["used_width"]),
                    waste_width=int(pattern["waste_width"]),
                )
            )

        return build_result_from_stage_plans(
            method_key="two_stage_greedy",
            method_name="二阶段齐头切贪心",
            case=case,
            runtime_seconds=0.0,
            stage_plans=stage_plans,
        )

    result, runtime_seconds = timed_call(_run)
    result.runtime_seconds = runtime_seconds
    return result

