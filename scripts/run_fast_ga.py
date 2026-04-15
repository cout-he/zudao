# -*- coding: utf-8 -*-
"""
快速版 GA 运行脚本
自动生成并保存独立的 GA 结果图文件。
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import SCALE_FACTOR, PANEL_WIDTH, DECODER_MODE, OUTPUT_DIR
from core.cutting_report import write_cutting_report
from core.data_loader import expand_demand
from core.decoder import merge_same_pattern_strips
from core.ga_engine_fast import GeneticAlgorithm
from core.visualization import (
    plot_compact_cutting_plan,
    plot_evolution_history,
    plot_stage_based_cutting_plan,
    plot_strip_details,
)


GA_FAST_CUTTING_PLAN = OUTPUT_DIR / "ga_fast_cutting_plan.png"
GA_FAST_EVOLUTION = OUTPUT_DIR / "ga_fast_evolution_history.png"
GA_FAST_STRIP_DETAILS = OUTPUT_DIR / "ga_fast_strip_details.png"


def build_plot_history(history):
    """
    兼容 history 中 best/avg 长度不一致的情况。
    """
    best = list(history["best_fitness"])
    avg = list(history["avg_fitness"])
    if len(best) == len(avg):
        return history

    trimmed = min(len(best), len(avg))
    return {
        "best_fitness": best[:trimmed],
        "avg_fitness": avg[:trimmed],
        "best_individual": history.get("best_individual"),
    }


def main():
    demand = {
        "Width": [230, 500, 547, 200, 400],
        "Length": [445, 833, 291, 555, 600],
        "num": [1000, 1000, 500, 666, 888],
        "Weight": [544.95, 3923.43, 423.76, 393.61, 1134.73],
    }

    print("=" * 60)
    print("   快速版遗传算法求解钢板切割优化问题")
    print("=" * 60)

    demand_df = pd.DataFrame(demand)
    print("\n原始需求:")
    print(demand_df)
    print(f"\n缩放因子: {SCALE_FACTOR}")
    print(f"解码模式: {DECODER_MODE}")

    items, type_info = expand_demand(demand)
    print(f"编码后小板数: {len(items)}")
    print("\n【开始遗传算法优化】")

    ga = GeneticAlgorithm(
        items,
        population_size=24,
        max_generations=60,
        crossover_rate=0.85,
        mutation_rate=0.22,
        elite_size=3,
    )
    ga.evolve(verbose=True)

    solution = ga.get_solution()
    merged_strips, repeat_counts = merge_same_pattern_strips(solution["strips"])

    real_total_length = solution["total_length"] * SCALE_FACTOR
    total_area_demand = (demand_df["Width"] * demand_df["Length"] * demand_df["num"]).sum()
    total_area_used = PANEL_WIDTH * real_total_length
    real_efficiency = 100 * total_area_demand / total_area_used

    print("\n" + "=" * 60)
    print("                   优化结果")
    print("=" * 60)
    print(f"还原后总切割长度: {real_total_length:.0f} mm")
    print(f"还原后切割条数: {solution['num_strips'] * SCALE_FACTOR}")
    print(f"材料利用率: {real_efficiency:.2f}%")
    print(f"不同切割模式数: {len(merged_strips)}")

    print("\n【生成快速版 GA 结果图】")
    plot_history = build_plot_history(ga.history)
    plot_evolution_history(
        plot_history,
        save_path=GA_FAST_EVOLUTION,
        show=False,
    )
    if DECODER_MODE.lower() == "stage_based":
        plot_stage_based_cutting_plan(
            solution["strips"],
            real_efficiency,
            save_path=GA_FAST_CUTTING_PLAN,
            show=False,
        )
    else:
        plot_compact_cutting_plan(
            merged_strips,
            repeat_counts,
            real_efficiency,
            save_path=GA_FAST_CUTTING_PLAN,
            show=False,
        )
    plot_strip_details(
        merged_strips,
        type_info,
        save_path=GA_FAST_STRIP_DETAILS,
        show=False,
    )

    report_path = OUTPUT_DIR / f"ga_fast_{DECODER_MODE}_cutting_report.txt"
    write_cutting_report(
        sheet_num=0,
        decoder_mode=DECODER_MODE,
        demand=demand,
        solution=solution,
        output_path=report_path,
    )

    print(f"已保存排版图: {GA_FAST_CUTTING_PLAN}")
    print(f"已保存进化曲线: {GA_FAST_EVOLUTION}")
    print(f"已保存条带明细图: {GA_FAST_STRIP_DETAILS}")
    print(f"已保存切割报告: {report_path}")
    print("=" * 60)

    return {
        "solution": solution,
        "merged_strips": merged_strips,
        "repeat_counts": repeat_counts,
        "real_efficiency": real_efficiency,
    }


if __name__ == "__main__":
    main()
