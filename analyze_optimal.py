# -*- coding: utf-8 -*-
"""
最优切割方案分析器
通过数学分析直接计算最优组合
"""

import sys
sys.path.append('D:/A-myprofile/zudao')

from config import PANEL_WIDTH, MIN_CUT_GAP
import itertools
import pandas as pd

# 产品数据
products = [
    {'id': 1, 'width': 230, 'length': 445, 'num': 1000},
    {'id': 2, 'width': 500, 'length': 833, 'num': 1000},
    {'id': 3, 'width': 547, 'length': 291, 'num': 500},
    {'id': 4, 'width': 200, 'length': 555, 'num': 666},
    {'id': 5, 'width': 400, 'length': 600, 'num': 888},
]

print("=" * 70)
print("               最优切割组合分析")
print("=" * 70)
print(f"\n大板宽度: {PANEL_WIDTH}mm, 最小纵切距离: {MIN_CUT_GAP}mm")
print("\n产品信息:")
for p in products:
    print(f"  T{p['id']}: {p['width']}mm × {p['length']}mm, 需求{p['num']}个")

# 生成所有可能的宽度组合
def generate_combinations():
    """生成所有满足宽度约束的组合"""
    combinations = []
    
    # 单产品组合
    for p in products:
        max_count = PANEL_WIDTH // p['width']
        for count in range(1, max_count + 1):
            total_width = count * p['width']
            if total_width >= MIN_CUT_GAP:  # 满足最小宽度
                waste = PANEL_WIDTH - total_width
                if waste < min(pr['width'] for pr in products):  # 浪费小于最小产品宽度
                    combinations.append({
                        'combo': {p['id']: count},
                        'width': total_width,
                        'waste_width': waste,
                        'length': p['length'],  # 单产品，长度就是该产品长度
                    })
    
    # 两产品组合
    for i, p1 in enumerate(products):
        for p2 in products[i:]:
            max1 = PANEL_WIDTH // p1['width']
            max2 = PANEL_WIDTH // p2['width']
            for c1 in range(0, max1 + 1):
                for c2 in range(0, max2 + 1):
                    if c1 == 0 and c2 == 0:
                        continue
                    if p1['id'] == p2['id'] and c1 + c2 > max1:
                        continue
                    total_width = c1 * p1['width'] + c2 * p2['width']
                    if MIN_CUT_GAP <= total_width <= PANEL_WIDTH:
                        waste = PANEL_WIDTH - total_width
                        if waste < min(pr['width'] for pr in products):
                            combo = {}
                            if c1 > 0:
                                combo[p1['id']] = c1
                            if c2 > 0:
                                combo[p2['id']] = combo.get(p2['id'], 0) + c2
                            length = max(
                                p1['length'] if c1 > 0 else 0,
                                p2['length'] if c2 > 0 else 0
                            )
                            combinations.append({
                                'combo': combo,
                                'width': total_width,
                                'waste_width': waste,
                                'length': length,
                            })
    
    # 三产品组合
    for i, p1 in enumerate(products):
        for j, p2 in enumerate(products[i:], i):
            for p3 in products[j:]:
                max1 = PANEL_WIDTH // p1['width']
                max2 = PANEL_WIDTH // p2['width']
                max3 = PANEL_WIDTH // p3['width']
                for c1 in range(0, min(max1 + 1, 4)):
                    for c2 in range(0, min(max2 + 1, 4)):
                        for c3 in range(0, min(max3 + 1, 4)):
                            if c1 == 0 and c2 == 0 and c3 == 0:
                                continue
                            total_width = c1*p1['width'] + c2*p2['width'] + c3*p3['width']
                            if MIN_CUT_GAP <= total_width <= PANEL_WIDTH:
                                waste = PANEL_WIDTH - total_width
                                if waste < min(pr['width'] for pr in products):
                                    combo = {}
                                    if c1 > 0:
                                        combo[p1['id']] = combo.get(p1['id'], 0) + c1
                                    if c2 > 0:
                                        combo[p2['id']] = combo.get(p2['id'], 0) + c2
                                    if c3 > 0:
                                        combo[p3['id']] = combo.get(p3['id'], 0) + c3
                                    lengths = [
                                        p1['length'] if c1 > 0 else 0,
                                        p2['length'] if c2 > 0 else 0,
                                        p3['length'] if c3 > 0 else 0,
                                    ]
                                    length = max(lengths)
                                    combinations.append({
                                        'combo': combo,
                                        'width': total_width,
                                        'waste_width': waste,
                                        'length': length,
                                    })
    
    # 去重
    unique = []
    seen = set()
    for c in combinations:
        key = tuple(sorted(c['combo'].items()))
        if key not in seen:
            seen.add(key)
            unique.append(c)
    
    return unique

combos = generate_combinations()
print(f"\n找到 {len(combos)} 种可行的宽度组合")

# 按利用率排序
for c in combos:
    c['width_util'] = c['width'] / PANEL_WIDTH * 100

combos.sort(key=lambda x: -x['width_util'])

print("\n宽度利用率最高的组合（前15个）:")
print("-" * 70)
for i, c in enumerate(combos[:15]):
    combo_str = " + ".join([f"T{k}×{v}" for k, v in sorted(c['combo'].items())])
    print(f"{i+1:2}. {combo_str:30} 宽度={c['width']:4}mm ({c['width_util']:.1f}%) 长度={c['length']}mm")

# 找出同长度的最优组合
print("\n\n【按长度分组的最优组合】")
print("-" * 70)
length_groups = {}
for c in combos:
    length = c['length']
    if length not in length_groups:
        length_groups[length] = []
    length_groups[length].append(c)

for length in sorted(length_groups.keys()):
    group = length_groups[length]
    group.sort(key=lambda x: -x['width_util'])
    best = group[0]
    combo_str = " + ".join([f"T{k}×{v}" for k, v in sorted(best['combo'].items())])
    print(f"长度 {length:4}mm: {combo_str:30} 宽度={best['width']:4}mm ({best['width_util']:.1f}%)")

# 计算理论最优解
print("\n\n【理论最优解分析】")
print("-" * 70)
print("如果每种产品都用最优的同长度组合：")

total_length = 0
total_area_demand = 0
for p in products:
    # 找该产品长度下宽度利用率最高的组合
    length = p['length']
    best_combo = None
    for c in combos:
        if c['length'] == length and p['id'] in c['combo']:
            if best_combo is None or c['width_util'] > best_combo['width_util']:
                best_combo = c
    
    if best_combo:
        # 计算需要多少条
        count_per_strip = best_combo['combo'].get(p['id'], 0)
        if count_per_strip > 0:
            strips_needed = (p['num'] + count_per_strip - 1) // count_per_strip
            length_needed = strips_needed * p['length']
            
            combo_str = " + ".join([f"T{k}×{v}" for k, v in sorted(best_combo['combo'].items())])
            print(f"T{p['id']}: 使用组合 [{combo_str}], 需要 {strips_needed} 条, 长度 {length_needed}mm")
            
            total_area_demand += p['width'] * p['length'] * p['num']

# 实际最优方案
print("\n\n【推荐切割方案】")
print("-" * 70)
print("基于宽度利用最大化的方案：")

# 手动设计最优方案
plan = [
    # (组合描述, 宽度, 长度, 重复次数)
    ("T2×2 + T4×1", 1200, 833, 500),   # 500×2 + 200 = 1200, 完成T2和部分T4
    ("T5×3", 1200, 600, 296),          # 400×3 = 1200, 完成T5
    ("T4×6", 1200, 555, 28),           # 200×6 = 1200, 完成剩余T4
    ("T1×5", 1150, 445, 200),          # 230×5 = 1150, 完成T1
    ("T3×2", 1094, 291, 250),          # 547×2 = 1094, 完成T3
]

total_length = 0
for desc, width, length, count in plan:
    strip_length = length * count
    total_length += strip_length
    util = width / PANEL_WIDTH * 100
    print(f"  {desc:20} 宽度利用={util:.1f}%, 重复{count}次, 长度={strip_length}mm")

total_area = PANEL_WIDTH * total_length
demand_area = sum(p['width'] * p['length'] * p['num'] for p in products)
efficiency = 100 * demand_area / total_area

print(f"\n总切割长度: {total_length:,}mm")
print(f"需求面积: {demand_area:,}mm²")
print(f"使用面积: {total_area:,}mm²")
print(f"材料利用率: {efficiency:.2f}%")
print("=" * 70)
