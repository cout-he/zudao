# -*- coding: utf-8 -*-
"""
使用 Sheet2 数据分别运行 simple / best_fit / stage_based 三种解码模式，
并输出最终切割排布图。
"""

import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import (
    SCALE_FACTOR,
    PANEL_WIDTH,
    OUTPUT_DIR,
    DEFAULT_DATA_FILE,
    POPULATION_SIZE,
    MAX_GENERATIONS,
    CROSSOVER_RATE,
    MUTATION_RATE,
    ELITE_SIZE,
)
from core.cutting_report import write_cutting_report
from core.data_loader import load_demand_from_excel, expand_demand
from core.decoder import merge_same_pattern_strips
from core.ga_engine_fast import GeneticAlgorithm
from core.visualization import plot_compact_cutting_plan, plot_stage_based_cutting_plan


DECODER_MODES = ["simple", "best_fit", "stage_based"]


def load_sheet2_demand():
    """
    Sheet2 中重量列为空，实验脚本在本地兜底填充为 1.0。
    权重不参与当前 GA 目标函数，仅用于维持 Item 结构完整。
    """
    wb = load_workbook(DEFAULT_DATA_FILE, data_only=True)
    ws = wb["Sheet2"]
    item_num = ws["B1"].value
    if item_num is None or item_num <= 0:
        raise ValueError("Sheet2 的产品数量读取失败")

    demand = {"Width": [], "Length": [], "num": [], "Weight": []}
    for i in range(item_num):
        row = i + 3
        width = ws[f"A{row}"].value
        length = ws[f"B{row}"].value
        num = ws[f"C{row}"].value
        weight = ws[f"D{row}"].value
        if width is None or length is None or num is None:
            raise ValueError(f"Sheet2 第 {i + 1} 行关键字段缺失")

        demand["Width"].append(width)
        demand["Length"].append(length)
        demand["num"].append(num)
        demand["Weight"].append(weight if weight not in (None, 0) else 1.0)

    return demand


def run_single_mode(items, demand, decoder_mode):
    ga = GeneticAlgorithm(
        items,
        population_size=POPULATION_SIZE,
        max_generations=MAX_GENERATIONS,
        crossover_rate=CROSSOVER_RATE,
        mutation_rate=MUTATION_RATE,
        elite_size=ELITE_SIZE,
        decoder_mode=decoder_mode,
    )
    ga.evolve(verbose=True)
    solution = ga.get_solution()

    real_total_length = solution["total_length"] * SCALE_FACTOR
    total_area_demand = sum(
        width * length * num
        for width, length, num in zip(demand["Width"], demand["Length"], demand["num"])
    )
    total_area_used = PANEL_WIDTH * real_total_length
    real_efficiency = 100 * total_area_demand / total_area_used if total_area_used else 0.0

    output_path = OUTPUT_DIR / f"sheet2_{decoder_mode}_cutting_plan.png"
    report_path = OUTPUT_DIR / f"sheet2_{decoder_mode}_cutting_report.txt"
    if decoder_mode == "stage_based":
        plot_stage_based_cutting_plan(
            solution["strips"],
            real_efficiency,
            save_path=output_path,
            show=False,
        )
    else:
        merged_strips, repeat_counts = merge_same_pattern_strips(solution["strips"])
        plot_compact_cutting_plan(
            merged_strips,
            repeat_counts,
            real_efficiency,
            save_path=output_path,
            show=False,
        )

    write_cutting_report(
        sheet_num=2,
        decoder_mode=decoder_mode,
        demand=demand,
        solution=solution,
        output_path=report_path,
    )

    return {
        "decoder_mode": decoder_mode,
        "total_length": real_total_length,
        "efficiency": real_efficiency,
        "num_strips": solution["num_strips"] * SCALE_FACTOR,
        "output_path": output_path,
        "report_path": report_path,
    }


def main():
    print("=" * 72)
    print("Sheet2 解码模式对比实验：simple / best_fit / stage_based")
    print("=" * 72)
    print(f"缩放因子: {SCALE_FACTOR}")
    print(f"种群大小: {POPULATION_SIZE}")
    print(f"最大代数: {MAX_GENERATIONS}")

    demand = load_sheet2_demand()
    items, _ = expand_demand(demand)
    print(f"Sheet2 编码后小板数: {len(items)}")

    results = []
    for decoder_mode in DECODER_MODES:
        print("\n" + "-" * 72)
        print(f"运行解码模式: {decoder_mode}")
        print("-" * 72)
        result = run_single_mode(items, demand, decoder_mode)
        results.append(result)
        print(
            f"{decoder_mode} 完成: 总长度={result['total_length']:.0f} mm, "
            f"利用率={result['efficiency']:.2f}%, "
            f"图片={result['output_path']}, 报告={result['report_path']}"
        )

    print("\n" + "=" * 72)
    print("实验结果汇总")
    print("=" * 72)
    for result in results:
        print(
            f"{result['decoder_mode']:<12} "
            f"总长度={result['total_length']:.0f} mm, "
            f"利用率={result['efficiency']:.2f}%, "
            f"切割条数={result['num_strips']}, "
            f"图片={result['output_path'].name}, "
            f"报告={result['report_path'].name}"
        )


if __name__ == "__main__":
    main()
