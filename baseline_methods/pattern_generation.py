# -*- coding: utf-8 -*-
"""Pattern-generation baseline with heuristic master selection."""

from __future__ import annotations

import math

from baseline_methods.common import (
    BaselineResult,
    GroupCase,
    StagePlan,
    build_result_from_stage_plans,
    timed_call,
)


OVER_AREA_PENALTY = 0.30
WASTE_WIDTH_PENALTY = 0.04
MAX_EXTRA_LANES = 1


def _enumerate_lane_patterns(widths: list[int], panel_width: int) -> list[tuple[int, ...]]:
    patterns: list[tuple[int, ...]] = []
    current = [0] * len(widths)

    def _dfs(index: int, remaining_width: int) -> None:
        if index >= len(widths):
            if any(current):
                patterns.append(tuple(current))
            return

        width = widths[index]
        max_count = remaining_width // width
        for count in range(max_count + 1):
            current[index] = count
            _dfs(index + 1, remaining_width - count * width)
        current[index] = 0

    _dfs(0, panel_width)
    return patterns


def _build_pattern_pool(case: GroupCase) -> list[dict]:
    widths = [spec.width for spec in case.specs]
    raw_patterns = _enumerate_lane_patterns(widths, case.panel_width)
    pattern_pool: list[dict] = []

    for stage_length in sorted({spec.length for spec in case.specs}):
        for lane_tuple in raw_patterns:
            produced_per_repeat = {}
            used_width = 0
            for index, spec in enumerate(case.specs):
                lane_count = lane_tuple[index]
                if lane_count <= 0:
                    continue
                pieces_per_lane = stage_length // spec.length
                if pieces_per_lane <= 0:
                    continue
                produced_per_repeat[spec.standard_spec] = lane_count * pieces_per_lane
                used_width += lane_count * spec.width

            if not produced_per_repeat or used_width <= 0:
                continue

            pattern_pool.append(
                {
                    "stage_length": stage_length,
                    "lane_counts": {
                        case.specs[index].standard_spec: lane_tuple[index]
                        for index in range(len(case.specs))
                    },
                    "produced_per_repeat": produced_per_repeat,
                    "used_width": used_width,
                    "waste_width": case.panel_width - used_width,
                }
            )
    return pattern_pool


def _score_pattern(case: GroupCase, remaining: dict[str, int], pattern: dict) -> tuple[float, float, int]:
    useful_area = 0
    over_area = 0
    useful_pieces = 0

    for spec in case.specs:
        produced = pattern["produced_per_repeat"].get(spec.standard_spec, 0)
        if produced <= 0:
            continue
        useful_pieces += min(remaining[spec.standard_spec], produced)
        useful_area += min(remaining[spec.standard_spec], produced) * spec.area_per_piece
        over_area += max(0, produced - remaining[spec.standard_spec]) * spec.area_per_piece

    stage_area = case.panel_width * pattern["stage_length"]
    normalized_score = 0.0
    if stage_area > 0:
        normalized_score = (
            useful_area
            - OVER_AREA_PENALTY * over_area
            - WASTE_WIDTH_PENALTY * pattern["waste_width"] * pattern["stage_length"]
        ) / stage_area

    return normalized_score, useful_area, useful_pieces


def _safe_repeat_count(remaining: dict[str, int], produced_per_repeat: dict[str, int]) -> int:
    floor_limits = []
    ceil_limits = []
    for spec_key, produced in produced_per_repeat.items():
        if produced <= 0:
            continue
        remaining_qty = remaining[spec_key]
        if remaining_qty >= produced:
            floor_limits.append(max(1, remaining_qty // produced))
        ceil_limits.append(max(1, math.ceil(remaining_qty / produced)))

    if floor_limits:
        return max(1, min(floor_limits))
    if ceil_limits:
        return 1
    return 1


def solve(case: GroupCase) -> BaselineResult:
    def _run() -> BaselineResult:
        remaining = {spec.standard_spec: spec.demand_qty for spec in case.specs}
        stage_plans: list[StagePlan] = []
        pattern_pool = _build_pattern_pool(case)
        max_iterations = 1000

        for iteration in range(max_iterations):
            if all(value <= 0 for value in remaining.values()):
                break

            best_pattern = None
            best_score = None
            for pattern in pattern_pool:
                score = _score_pattern(case, remaining, pattern)
                if best_score is None or score > best_score:
                    best_pattern = pattern
                    best_score = score

            if best_pattern is None:
                break

            repeat_count = _safe_repeat_count(remaining, best_pattern["produced_per_repeat"])
            produced_total = {
                spec_key: int(qty * repeat_count)
                for spec_key, qty in best_pattern["produced_per_repeat"].items()
            }
            for spec_key, produced in produced_total.items():
                remaining[spec_key] -= produced

            stage_plans.append(
                StagePlan(
                    stage_index=iteration + 1,
                    repeat_count=int(repeat_count),
                    stage_length=int(best_pattern["stage_length"]),
                    lane_counts={
                        spec_key: int(lane_count)
                        for spec_key, lane_count in best_pattern["lane_counts"].items()
                    },
                    produced_per_repeat={
                        spec_key: int(qty)
                        for spec_key, qty in best_pattern["produced_per_repeat"].items()
                    },
                    produced_total=produced_total,
                    used_width=int(best_pattern["used_width"]),
                    waste_width=int(best_pattern["waste_width"]),
                )
            )

        return build_result_from_stage_plans(
            method_key="pattern_generation",
            method_name="版型生成法",
            case=case,
            runtime_seconds=0.0,
            stage_plans=stage_plans,
        )

    result, runtime_seconds = timed_call(_run)
    result.runtime_seconds = runtime_seconds
    return result

