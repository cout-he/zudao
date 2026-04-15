# -*- coding: utf-8 -*-
"""
交互式 GA 入口：
1 -> simple
2 -> best_fit
3 -> stage_based
4 -> 三种模式全部运行，仅输出利用率最高的方案
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import (  # noqa: E402
    CROSSOVER_RATE,
    DEFAULT_DATA_FILE,
    ELITE_SIZE,
    MAX_GENERATIONS,
    MUTATION_RATE,
    OUTPUT_DIR,
    PANEL_WIDTH,
    POPULATION_SIZE,
    SCALE_FACTOR,
)

MODE_MENU = {
    "1": "simple",
    "2": "best_fit",
    "3": "stage_based",
    "4": "all",
}

ALL_DECODER_MODES = ["simple", "best_fit", "stage_based"]


def load_runtime_modules():
    try:
        from core.cutting_report import write_cutting_report
        from core.data_loader import expand_demand, load_demand_from_excel
        from core.decoder import merge_same_pattern_strips
        from core.ga_engine_fast import GeneticAlgorithm
        from core.visualization import (
            plot_compact_cutting_plan,
            plot_stage_based_cutting_plan,
        )
    except ModuleNotFoundError as exc:
        missing_module = exc.name or "未知模块"
        print("运行失败：当前 Python 解释器缺少项目依赖。")
        print(f"缺少模块: {missing_module}")
        print(f"当前解释器: {sys.executable}")
        print("")
        print("可选处理方式：")
        print("1. 改用你当前已装好依赖的环境来运行。")
        print("2. 在这个解释器里安装依赖，例如：")
        print(
            f'   "{sys.executable}" -m pip install pandas openpyxl matplotlib numpy'
        )
        raise SystemExit(1) from exc

    return {
        "write_cutting_report": write_cutting_report,
        "expand_demand": expand_demand,
        "load_demand_from_excel": load_demand_from_excel,
        "merge_same_pattern_strips": merge_same_pattern_strips,
        "GeneticAlgorithm": GeneticAlgorithm,
        "plot_compact_cutting_plan": plot_compact_cutting_plan,
        "plot_stage_based_cutting_plan": plot_stage_based_cutting_plan,
    }


def prompt_decoder_choice():
    print("=" * 60)
    print("遗传算法排样求解")
    print("=" * 60)
    print("请选择解码方式：")
    print("1. simple")
    print("2. best_fit")
    print("3. stage_based")
    print("4. 三种模式都跑一遍，仅输出利用率最高的方案")

    while True:
        choice = input("请输入 1 / 2 / 3 / 4: ").strip()
        if choice in MODE_MENU:
            return MODE_MENU[choice]
        print("输入无效，请重新输入。")


def prompt_sheet_num():
    while True:
        raw = input("请输入产品数据表编号: ").strip()
        try:
            sheet_num = int(raw)
            if sheet_num <= 0:
                raise ValueError
            return sheet_num
        except ValueError:
            print("数据表编号必须是正整数，请重新输入。")


def calculate_real_efficiency(demand, encoded_total_length):
    total_demand_area = sum(
        width * length * num
        for width, length, num in zip(demand["Width"], demand["Length"], demand["num"])
    )
    real_total_length = encoded_total_length * SCALE_FACTOR
    total_panel_area = PANEL_WIDTH * real_total_length
    if total_panel_area <= 0:
        return 0.0, 0
    return 100 * total_demand_area / total_panel_area, real_total_length


def run_single_mode(items, demand, decoder_mode, runtime):
    ga = runtime["GeneticAlgorithm"](
        items,
        population_size=POPULATION_SIZE,
        max_generations=MAX_GENERATIONS,
        crossover_rate=CROSSOVER_RATE,
        mutation_rate=MUTATION_RATE,
        elite_size=ELITE_SIZE,
        decoder_mode=decoder_mode,
    )

    best_individual, best_fitness = ga.evolve(verbose=True)
    solution = ga.get_solution(best_individual)
    real_efficiency, real_total_length = calculate_real_efficiency(
        demand, solution["total_length"]
    )

    return {
        "decoder_mode": decoder_mode,
        "best_fitness": best_fitness,
        "solution": solution,
        "real_efficiency": real_efficiency,
        "real_total_length": real_total_length,
    }


def print_mode_result(result):
    solution = result["solution"]
    print("-" * 60)
    print(f"解码方式: {result['decoder_mode']}")
    print(f"编码总长度: {solution['total_length']:.0f} mm")
    print(f"还原总长度: {result['real_total_length']:.0f} mm")
    print(f"材料利用率: {result['real_efficiency']:.2f}%")
    print(f"条带/阶段数: {solution['num_strips']}")
    print(f"惩罚值: {solution['penalty']}")


def save_outputs(sheet_num, demand, result, runtime):
    decoder_mode = result["decoder_mode"]
    solution = result["solution"]
    efficiency = result["real_efficiency"]

    image_path = OUTPUT_DIR / f"sheet{sheet_num}_{decoder_mode}_cutting_plan.png"
    report_path = OUTPUT_DIR / f"sheet{sheet_num}_{decoder_mode}_cutting_report.txt"

    if decoder_mode == "stage_based":
        runtime["plot_stage_based_cutting_plan"](
            solution["strips"],
            efficiency,
            save_path=image_path,
            show=False,
        )
    else:
        merged_strips, repeat_counts = runtime["merge_same_pattern_strips"](solution["strips"])
        runtime["plot_compact_cutting_plan"](
            merged_strips,
            repeat_counts,
            efficiency,
            save_path=image_path,
            show=False,
        )

    runtime["write_cutting_report"](
        sheet_num=sheet_num,
        decoder_mode=decoder_mode,
        demand=demand,
        solution=solution,
        output_path=report_path,
    )

    return image_path, report_path


def choose_best_result(results):
    return max(
        results,
        key=lambda item: (
            item["real_efficiency"],
            -item["real_total_length"],
            -item["solution"]["penalty"],
        ),
    )


def main():
    runtime = load_runtime_modules()
    decoder_choice = prompt_decoder_choice()
    sheet_num = prompt_sheet_num()

    print("\n正在加载数据...")
    try:
        demand = runtime["load_demand_from_excel"](
            filepath=DEFAULT_DATA_FILE, sheet_num=sheet_num
        )
    except Exception as exc:
        print(f"数据加载失败: {exc}")
        return

    items, _ = runtime["expand_demand"](demand)
    print(f"已加载 Sheet{sheet_num}，编码后个体数: {len(items)}")

    if decoder_choice == "all":
        print("\n开始依次运行 3 种解码方式...\n")
        all_results = []
        for decoder_mode in ALL_DECODER_MODES:
            print(f"[运行中] {decoder_mode}")
            result = run_single_mode(items, demand, decoder_mode, runtime)
            all_results.append(result)
            print_mode_result(result)

        best_result = choose_best_result(all_results)
        image_path, report_path = save_outputs(sheet_num, demand, best_result, runtime)

        print("\n" + "=" * 60)
        print("三种模式运行完成，已输出利用率最高的方案")
        print("=" * 60)
        print(f"最佳解码方式: {best_result['decoder_mode']}")
        print(f"最佳利用率: {best_result['real_efficiency']:.2f}%")
        print(f"排版图: {image_path}")
        print(f"切割报告: {report_path}")
        return

    print(f"\n开始运行解码方式: {decoder_choice}\n")
    result = run_single_mode(items, demand, decoder_choice, runtime)
    image_path, report_path = save_outputs(sheet_num, demand, result, runtime)

    print("\n" + "=" * 60)
    print("求解完成")
    print("=" * 60)
    print_mode_result(result)
    print(f"排版图: {image_path}")
    print(f"切割报告: {report_path}")


if __name__ == "__main__":
    main()
