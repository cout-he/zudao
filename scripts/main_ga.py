# -*- coding: utf-8 -*-
"""
遗传算法求解钢板切割优化问题 - 主程序入口
"""

import sys
from pathlib import Path

# 添加当前目录到路径
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import (
    POPULATION_SIZE, MAX_GENERATIONS, 
    CROSSOVER_RATE, MUTATION_RATE, PANEL_WIDTH, MIN_CUT_GAP, SCALE_FACTOR,
    DECODER_MODE, OUTPUT_DIR
)
from core.data_loader import load_demand_from_excel, expand_demand
from core.ga_engine_fast import GeneticAlgorithm
from core.decoder import decode, calculate_efficiency, get_cutting_plan, merge_same_pattern_strips
from core.visualization import (
    plot_compact_cutting_plan, plot_evolution_history,
    plot_stage_based_cutting_plan,
    plot_strip_details, print_solution_summary
)

import pandas as pd


def main():
    """主函数"""
    print("=" * 60)
    print("       遗传算法求解钢板切割优化问题")
    print("=" * 60)
    
    # 打印配置参数
    print("\n【算法参数】")
    print(f"  大板宽度: {PANEL_WIDTH} mm")
    print(f"  最小纵切距离: {MIN_CUT_GAP} mm")
    print(f"  种群大小: {POPULATION_SIZE}")
    print(f"  最大迭代代数: {MAX_GENERATIONS}")
    print(f"  交叉概率: {CROSSOVER_RATE}")
    print(f"  变异概率: {MUTATION_RATE}")
    print(f"  数据缩放因子: {SCALE_FACTOR}")
    print(f"  解码模式: {DECODER_MODE}")
    if SCALE_FACTOR > 1:
        print(f"  (每{SCALE_FACTOR}个同类板编码为1个，最后结果×{SCALE_FACTOR})")
    print("-" * 60)
    
    # 获取用户输入
    try:
        sheet_num = int(input("\n请输入产品数据表编号: "))
    except ValueError:
        print("输入无效，使用默认值 1")
        sheet_num = 1
    
    # 加载数据
    print("\n【加载数据】")
    try:
        demand = load_demand_from_excel(sheet_num=sheet_num)
    except Exception as e:
        print(f"数据加载失败: {e}")
        return
    
    # 显示原始需求
    demand_df = pd.DataFrame(demand)
    print("\n原始需求:")
    print(demand_df.to_string(index=True))
    
    total_original = sum(demand['num'])
    print(f"\n原始小板总数: {total_original}")
    
    # 展开需求
    items, type_info = expand_demand(demand)
    print(f"缩放后编码的小板数: {len(items)}")
    
    # 检查数据量
    if len(items) > 3000:
        print(f"\n警告: 小板数量较多({len(items)})，建议在config.py中增大SCALE_FACTOR")
        continue_flag = input("是否继续? (y/n): ")
        if continue_flag.lower() != 'y':
            return
    
    # 创建遗传算法实例
    print("\n【开始遗传算法优化】")
    ga = GeneticAlgorithm(
        items,
        population_size=POPULATION_SIZE,
        max_generations=MAX_GENERATIONS,
        crossover_rate=CROSSOVER_RATE,
        mutation_rate=MUTATION_RATE
    )
    
    # 运行进化
    best_individual, best_fitness = ga.evolve(verbose=True)
    
    # 获取最终解决方案
    solution = ga.get_solution()
    
    # 还原真实长度（考虑缩放）
    real_total_length = solution['total_length'] * SCALE_FACTOR
    
    # 打印结果摘要
    print("\n" + "=" * 60)
    print("                   优化结果")
    print("=" * 60)
    
    # 合并相同模式的条
    merged_strips, repeat_counts = merge_same_pattern_strips(solution['strips'])
    
    print(f"\n【切割方案摘要】")
    print(f"  编码后总切割长度: {solution['total_length']:.0f} mm")
    print(f"  还原后总切割长度: {real_total_length:.0f} mm")
    print(f"  编码后切割条数: {solution['num_strips']}")
    print(f"  还原后切割条数: {solution['num_strips'] * SCALE_FACTOR}")
    print(f"  合并后不同模式数: {len(merged_strips)}")
    
    # 计算真实效率
    total_area_demand = (demand_df['Width'] * demand_df['Length'] * demand_df['num']).sum()
    total_area_used = PANEL_WIDTH * real_total_length
    real_efficiency = 100 * total_area_demand / total_area_used
    
    print(f"\n【材料使用统计】")
    print(f"  需求总面积: {total_area_demand:,.0f} mm²")
    print(f"  实际使用面积: {total_area_used:,.0f} mm²")
    print(f"  浪费面积: {total_area_used - total_area_demand:,.0f} mm²")
    print(f"  材料利用率: {real_efficiency:.2f}%")
    
    # 打印合并后的切割模式
    print(f"\n【切割模式详情】（共{len(merged_strips)}种模式）")
    print("-" * 60)
    
    for i, (strip, count) in enumerate(zip(merged_strips, repeat_counts)):
        # 统计各类型数量
        type_counts = {}
        for item in strip.items:
            type_id = item.type_id
            if type_id not in type_counts:
                type_counts[type_id] = 0
            type_counts[type_id] += 1
        
        type_str = ", ".join([f"T{k+1}×{v}" for k, v in sorted(type_counts.items())])
        real_count = count * SCALE_FACTOR
        
        print(f"模式{i+1}: 重复{real_count}次, 长度={strip.strip_length}mm, "
              f"宽度={strip.used_width}mm")
        print(f"        组成: {type_str}")
    
    print("=" * 60)
    
    # 可视化
    print("\n【生成可视化图表】")
    
    # 绘制进化曲线
    plot_evolution_history(
        ga.history,
        save_path=OUTPUT_DIR / 'ga_fast_evolution_history.png',
        show=False
    )
    
    # 绘制切割方案（只绘制不同的模式）
    max_strips_to_plot = min(20, len(merged_strips))
    if len(merged_strips) > max_strips_to_plot:
        print(f"切割模式较多，仅绘制前{max_strips_to_plot}种")
    
    if DECODER_MODE.lower() == 'stage_based':
        plot_stage_based_cutting_plan(
            solution['strips'],
            real_efficiency,
            save_path=OUTPUT_DIR / 'ga_fast_cutting_plan.png',
            show=False
        )
    else:
        plot_compact_cutting_plan(
            merged_strips[:max_strips_to_plot],
            repeat_counts[:max_strips_to_plot],
            real_efficiency,
            save_path=OUTPUT_DIR / 'ga_fast_cutting_plan.png',
            show=False
        )
    
    # 绘制详细信息
    plot_strip_details(
        merged_strips,
        type_info,
        save_path=OUTPUT_DIR / 'ga_fast_strip_details.png',
        show=False
    )
    
    print("\n优化完成!")
    print("=" * 60)
    
    return solution


if __name__ == '__main__':
    solution = main()
