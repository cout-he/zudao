# -*- coding: utf-8 -*-
"""
线性规划求解最优切割方案
使用所有高利用率的宽度组合，通过线性规划找到最优使用次数
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import PANEL_WIDTH, MIN_CUT_GAP

# 产品数据
products = {
    1: {'width': 230, 'length': 445, 'num': 1000},
    2: {'width': 500, 'length': 833, 'num': 1000},
    3: {'width': 547, 'length': 291, 'num': 500},
    4: {'width': 200, 'length': 555, 'num': 666},
    5: {'width': 400, 'length': 600, 'num': 888},
}

# 可行的切割模式 (宽度组合 + 长度)
# 格式: {产品ID: 数量}, 宽度, 长度
patterns = [
    # 高利用率组合 (>95%)
    ({2: 1, 3: 1, 4: 1}, 1247, 833),   # 99.8% - T2+T3+T4，长度取最大833
    ({1: 3, 3: 1}, 1237, 445),          # 99.0% - T1×3+T3，长度取445(T1的长度)
    ({1: 1, 2: 2}, 1230, 833),          # 98.4% - T1+T2×2
    ({1: 1, 4: 5}, 1230, 555),          # 98.4% - T1+T4×5
    ({1: 1, 4: 1, 5: 2}, 1230, 600),    # 98.4% - T1+T4+T5×2
    ({1: 1, 4: 3, 5: 1}, 1230, 600),    # 98.4% - T1+T4×3+T5
    ({1: 2, 3: 1, 4: 1}, 1207, 555),    # 96.6% - T1×2+T3+T4
    
    # 96%利用率组合
    ({4: 6}, 1200, 555),                # 96.0% - T4×6
    ({5: 3}, 1200, 600),                # 96.0% - T5×3
    ({2: 2, 4: 1}, 1200, 833),          # 96.0% - T2×2+T4
    ({4: 2, 5: 2}, 1200, 600),          # 96.0% - T4×2+T5×2
    ({4: 4, 5: 1}, 1200, 600),          # 96.0% - T4×4+T5
    
    # 纯产品组合 (备用)
    ({1: 5}, 1150, 445),                # 92.0% - T1×5
    ({2: 2}, 1000, 833),                # 80.0% - T2×2
    ({3: 2}, 1094, 291),                # 87.5% - T3×2
]

print("=" * 70)
print("          贪婪算法寻找最优组合")
print("=" * 70)

# 剩余需求
remaining = {k: v['num'] for k, v in products.items()}

# 贪婪策略：按利用率从高到低尝试
# 利用率 = (组合宽度 * 产出数量) / (PANEL_WIDTH * 长度 * 使用次数)

def calc_pattern_efficiency(pattern, combo, width, length):
    """计算一个模式的整体效率"""
    area_produced = sum(
        products[pid]['width'] * products[pid]['length'] * cnt 
        for pid, cnt in combo.items()
    )
    area_used = PANEL_WIDTH * length
    return area_produced / area_used

# 计算每个模式的效率
pattern_info = []
for combo, width, length in patterns:
    eff = calc_pattern_efficiency(None, combo, width, length)
    pattern_info.append({
        'combo': combo,
        'width': width,
        'length': length,
        'efficiency': eff,
    })

# 按效率排序
pattern_info.sort(key=lambda x: -x['efficiency'])

print("\n模式按效率排序：")
for i, p in enumerate(pattern_info):
    combo_str = " + ".join([f"T{k}×{v}" for k, v in sorted(p['combo'].items())])
    print(f"{i+1:2}. {combo_str:30} 宽度={p['width']:4}mm 长度={p['length']:3}mm 效率={p['efficiency']*100:.1f}%")

# 贪婪分配
solution = []
total_length = 0
total_area_produced = 0

print("\n" + "=" * 70)
print("              开始贪婪分配")
print("=" * 70)

max_iterations = 100
for iteration in range(max_iterations):
    best_pattern = None
    best_count = 0
    best_score = -1
    
    # 对每个模式，计算可以使用多少次
    for p in pattern_info:
        combo = p['combo']
        # 计算最多可以使用多少次
        max_count = float('inf')
        for pid, cnt in combo.items():
            if cnt > 0:
                available = remaining[pid]
                max_count = min(max_count, available // cnt)
        
        if max_count > 0:
            # 用效率作为分数
            score = p['efficiency']
            if score > best_score:
                best_score = score
                best_pattern = p
                best_count = int(max_count)
    
    if best_pattern is None or best_count == 0:
        break
    
    # 使用这个模式
    combo = best_pattern['combo']
    length = best_pattern['length']
    
    # 更新剩余需求
    for pid, cnt in combo.items():
        remaining[pid] -= cnt * best_count
    
    # 记录
    strip_length = length * best_count
    total_length += strip_length
    for pid, cnt in combo.items():
        total_area_produced += products[pid]['width'] * products[pid]['length'] * cnt * best_count
    
    combo_str = " + ".join([f"T{k}×{v}" for k, v in sorted(combo.items())])
    print(f"使用模式 [{combo_str}] × {best_count}次, 长度={strip_length}mm")
    
    solution.append({
        'combo': combo,
        'width': best_pattern['width'],
        'length': length,
        'count': best_count,
    })

# 检查剩余
print("\n剩余需求:")
any_remaining = False
for pid, cnt in remaining.items():
    if cnt > 0:
        print(f"  T{pid}: {cnt}个")
        any_remaining = True

# 处理剩余（用单产品模式）
if any_remaining:
    print("\n处理剩余需求：")
    for pid, cnt in remaining.items():
        if cnt > 0:
            p = products[pid]
            # 计算一条可以放几个
            n_per_strip = PANEL_WIDTH // p['width']
            strips_needed = (cnt + n_per_strip - 1) // n_per_strip
            strip_length = p['length'] * strips_needed
            total_length += strip_length
            actual_produced = min(cnt, n_per_strip * strips_needed)
            total_area_produced += p['width'] * p['length'] * actual_produced
            print(f"  T{pid}: {n_per_strip}个/条 × {strips_needed}条 = {strip_length}mm")
            
            solution.append({
                'combo': {pid: n_per_strip},
                'width': n_per_strip * p['width'],
                'length': p['length'],
                'count': strips_needed,
            })

# 最终结果
print("\n" + "=" * 70)
print("                 最终方案")
print("=" * 70)

total_area_used = PANEL_WIDTH * total_length
total_demand = sum(p['width'] * p['length'] * p['num'] for p in products.values())
efficiency = 100 * total_demand / total_area_used

print(f"\n{'模式':40} {'宽度':>8} {'长度':>8} {'次数':>6} {'长度贡献':>12}")
print("-" * 80)
for s in solution:
    combo_str = " + ".join([f"T{k}×{v}" for k, v in sorted(s['combo'].items())])
    length_contrib = s['length'] * s['count']
    width_util = s['width'] / PANEL_WIDTH * 100
    print(f"{combo_str:40} {s['width']:>7}mm {s['length']:>7}mm {s['count']:>6} {length_contrib:>11}mm")

print("-" * 80)
print(f"\n总切割长度: {total_length:,}mm")
print(f"需求面积: {total_demand:,}mm²")
print(f"使用面积: {total_area_used:,}mm²")
print(f"材料利用率: {efficiency:.2f}%")

# 验证产出
print("\n产出验证:")
output = {k: 0 for k in products.keys()}
for s in solution:
    for pid, cnt in s['combo'].items():
        output[pid] += cnt * s['count']

for pid in products.keys():
    demand = products[pid]['num']
    produced = output[pid]
    status = "✓" if produced >= demand else "✗"
    print(f"  T{pid}: 需求{demand}, 产出{produced} {status}")
