# -*- coding: utf-8 -*-
"""
快速测试脚本 - 优化版
"""

import sys
sys.path.append('D:/A-myprofile/zudao')

from config import SCALE_FACTOR, PANEL_WIDTH, DECODER_MODE
from data_loader import expand_demand
from ga_engine_fast import GeneticAlgorithm
from decoder import merge_same_pattern_strips
import pandas as pd

# 直接定义5种产品的需求数据
demand = {
    'Width': [230, 500, 547, 200, 400],
    'Length': [445, 833, 291, 555, 600],
    'num': [1000, 1000, 500, 666, 888],
    'Weight': [544.95, 3923.43, 423.76, 393.61, 1134.73]
}

print('=' * 60)
print('   遗传算法求解钢板切割优化问题')
print('=' * 60)
sys.stdout.flush()

demand_df = pd.DataFrame(demand)
print('\n原始需求 (5种产品):')
print(demand_df)
print(f'\n缩放因子: {SCALE_FACTOR}')
print(f'解码模式: {DECODER_MODE}')
sys.stdout.flush()

# 展开需求
items, type_info = expand_demand(demand)
print(f'编码后小板数: {len(items)}')
print('\n【开始遗传算法优化】')
sys.stdout.flush()

# 运行遗传算法
ga = GeneticAlgorithm(
    items, 
    population_size=24,        # 快速模式
    max_generations=60,        # 快速模式
    crossover_rate=0.85,
    mutation_rate=0.22,
    elite_size=3
)
best_individual, best_fitness = ga.evolve(verbose=True)

# 获取结果
solution = ga.get_solution()
real_total_length = solution['total_length'] * SCALE_FACTOR

# 计算效率
total_area_demand = (demand_df['Width'] * demand_df['Length'] * demand_df['num']).sum()
total_area_used = PANEL_WIDTH * real_total_length
real_efficiency = 100 * total_area_demand / total_area_used

print()
print('=' * 60)
print('                   优化结果')
print('=' * 60)
print(f'还原后总切割长度: {real_total_length:.0f} mm')
print(f'还原后切割条数: {solution["num_strips"] * SCALE_FACTOR}')
print(f'材料利用率: {real_efficiency:.2f}%')
print(f'需求总面积: {total_area_demand:,.0f} mm^2')
print(f'实际使用面积: {total_area_used:,.0f} mm^2')
print(f'浪费面积: {total_area_used - total_area_demand:,.0f} mm^2')

# 合并相同模式
merged, counts = merge_same_pattern_strips(solution['strips'])
print(f'\n不同切割模式数: {len(merged)}')
print('\n【切割模式详情】')
print('-' * 60)
for i, (s, c) in enumerate(zip(merged, counts)):
    tc = {}
    for item in s.items:
        tc[item.type_id] = tc.get(item.type_id, 0) + 1
    ts = ', '.join([f'T{k+1}×{v}' for k, v in sorted(tc.items())])
    real_count = c * SCALE_FACTOR
    print(f'模式{i+1}: 重复{real_count}次, 长度={s.strip_length}mm, '
          f'宽度={s.used_width}mm, 组成: {ts}')

print('=' * 60)
