# -*- coding: utf-8 -*-
"""
解码器模块 - 将染色体（排列顺序）解码为切割方案
这是遗传算法的核心逻辑

关键概念：
- 一条Strip（切割条）的长度由其中最长的小板决定
- 宽度方向尽量填满，避免浪费
- 长度相近的小板放在一起可以减少浪费
"""

import math
from functools import lru_cache
from itertools import product

from core.config import (
    PANEL_WIDTH,
    MIN_CUT_GAP,
    PENALTY_VALUE,
    DECODER_MODE,
    VERTICAL_CUT_INCLUSIVE,
    PATTERN_TOP_CANDIDATES,
    PATTERN_MIN_SAVINGS,
)


class Strip:
    """一条大板（切割条）的数据结构"""
    def __init__(self):
        self.items = []             # 该条包含的小板
        self.used_width = 0         # 已使用的宽度
        self.strip_length = 0       # 该条的长度（取决于最长的小板）
    
    def add_item(self, item):
        """添加小板到当前条"""
        self.items.append(item)
        self.used_width += item.width
        # 长度取最长的
        if item.length > self.strip_length:
            self.strip_length = item.length
    
    def can_add(self, item):
        """检查是否还能添加该小板（宽度方向）"""
        return (self.used_width + item.width) <= PANEL_WIDTH
    
    def get_remain_width(self):
        """获取剩余宽度"""
        return PANEL_WIDTH - self.used_width
    
    def is_valid(self):
        """检查该条是否满足最小纵切距离约束"""
        # 如果条为空，不算有效
        if self.used_width == 0:
            return True
        # 检查是否满足最小宽度约束
        return self.used_width >= MIN_CUT_GAP
    
    def get_waste_area(self):
        """计算该条的浪费面积"""
        # 浪费 = 宽度方向的空隙 + 长度方向的损耗
        width_waste = PANEL_WIDTH - self.used_width
        # 长度方向：每个小板与最长板的差值
        length_waste = sum(self.strip_length - item.length for item in self.items)
        return width_waste * self.strip_length + sum(item.width * (self.strip_length - item.length) for item in self.items)
    
    def __repr__(self):
        return f"Strip(width={self.used_width}, length={self.strip_length}, items={len(self.items)})"


def _item_width_is_valid(width):
    if VERTICAL_CUT_INCLUSIVE:
        return width >= MIN_CUT_GAP
    return width > MIN_CUT_GAP


def _strip_constraint_penalty(strip):
    penalty = 0
    if strip.used_width > 0 and strip.used_width < MIN_CUT_GAP:
        penalty += PENALTY_VALUE
    for item in strip.items:
        if not _item_width_is_valid(item.width):
            penalty += PENALTY_VALUE
    return penalty


@lru_cache(maxsize=16)
def _build_pattern_library(type_specs):
    """
    为当前物料规格生成可行 pattern 库。
    pattern 的目标不是只追求宽度占满，而是优先追求“比单独生产更省长度”。
    """
    widths = [spec[1] for spec in type_specs]
    lengths = [spec[2] for spec in type_specs]
    max_counts = [PANEL_WIDTH // width for width in widths]
    standalone_length_per_item = [
        length / max(1, PANEL_WIDTH // width) for width, length in zip(widths, lengths)
    ]

    patterns = []
    for counts in product(*[range(limit + 1) for limit in max_counts]):
        if not any(counts):
            continue

        used_width = sum(count * width for count, width in zip(counts, widths))
        if used_width <= 0 or used_width > PANEL_WIDTH:
            continue

        active = [idx for idx, count in enumerate(counts) if count > 0]
        if any(not _item_width_is_valid(widths[idx]) for idx in active):
            continue

        strip_length = max(lengths[idx] for idx in active)
        produced_area = sum(
            counts[idx] * widths[idx] * lengths[idx] for idx in active
        )
        sheet_area = PANEL_WIDTH * strip_length
        efficiency = produced_area / sheet_area if sheet_area else 0.0

        standalone_length = sum(
            counts[idx] * standalone_length_per_item[idx] for idx in active
        )
        savings = standalone_length - strip_length
        if savings < PATTERN_MIN_SAVINGS:
            continue

        patterns.append(
            {
                "counts": counts,
                "used_width": used_width,
                "strip_length": strip_length,
                "efficiency": efficiency,
                "savings": savings,
                "waste_width": PANEL_WIDTH - used_width,
            }
        )

    patterns.sort(
        key=lambda p: (
            -round(p["savings"], 6),
            -round(p["efficiency"], 6),
            p["waste_width"],
            p["strip_length"],
        )
    )
    return tuple(patterns)


def _get_type_specs(items):
    specs = {}
    for item in items:
        specs[item.type_id] = (item.type_id, item.width, item.length)
    return tuple(specs[key] for key in sorted(specs))


def decode(individual, items):
    """
    解码函数：将染色体（索引排列）解码为切割方案
    
    核心逻辑：按照染色体顺序依次取小板，尽量放入当前条，
    放不下时结算当前条并开启新条。
    
    参数:
        individual: list of int，小板的索引排列顺序
        items: list of Item，所有小板的列表
    
    返回:
        total_length: float，总消耗的大板长度
        strips: list of Strip，切割方案
        penalty: float，违反约束的惩罚值
    """
    strips = []
    current_strip = Strip()
    penalty = 0
    
    for idx in individual:
        item = items[idx]
        
        # 尝试放入当前条（宽度方向）
        if current_strip.can_add(item):
            current_strip.add_item(item)
        else:
            # 当前条放不下了，结算当前条
            if len(current_strip.items) > 0:
                # 检查最小纵切距离约束
                if not current_strip.is_valid():
                    penalty += PENALTY_VALUE
                strips.append(current_strip)
            
            # 开启新的一条
            current_strip = Strip()
            current_strip.add_item(item)
    
    # 处理最后一条
    if len(current_strip.items) > 0:
        if not current_strip.is_valid():
            penalty += PENALTY_VALUE
        strips.append(current_strip)
    
    # 计算总长度（所有条的长度之和）
    total_length = sum(strip.strip_length for strip in strips)
    
    return total_length, strips, penalty


def decode_best_fit(individual, items):
    """
    Best Fit解码器：尝试将每个板子放入能最小化浪费的现有条中
    
    优化策略：
    1. 优先放入长度完全相同的条
    2. 其次选择长度相近且宽度能容纳的条
    3. 如果没有合适的条，开启新条
    """
    strips = []
    penalty = 0
    
    for idx in individual:
        item = items[idx]
        
        best_strip_idx = -1
        best_score = float('inf')
        
        # 寻找最佳的现有条
        for i, strip in enumerate(strips):
            if strip.can_add(item):
                remain_width = strip.get_remain_width() - item.width
                
                # 长度完全匹配的情况（最优）
                if item.length == strip.strip_length:
                    score = -10000 + remain_width  # 非常优先
                else:
                    # 计算放入后的浪费
                    length_diff = abs(strip.strip_length - item.length)
                    new_length = max(strip.strip_length, item.length)
                    length_waste = (new_length - strip.strip_length) * strip.used_width
                    
                    # 如果新板更长，惩罚更重
                    if item.length > strip.strip_length:
                        length_waste *= 2
                    
                    score = length_waste + length_diff
                
                # 能填满宽度是好事
                if 0 <= remain_width < MIN_CUT_GAP:
                    score -= 1000
                
                if score < best_score:
                    best_score = score
                    best_strip_idx = i
        
        if best_strip_idx >= 0:
            strips[best_strip_idx].add_item(item)
        else:
            new_strip = Strip()
            new_strip.add_item(item)
            strips.append(new_strip)
    
    for strip in strips:
        if not strip.is_valid():
            penalty += PENALTY_VALUE
    
    total_length = sum(strip.strip_length for strip in strips)
    return total_length, strips, penalty


def decode_same_length_first(individual, items):
    """
    同长度优先解码器：优先把相同长度的板子组合在一起
    这是减少长度浪费的关键策略
    """
    # 按长度分组
    length_groups = {}
    for idx in individual:
        item = items[idx]
        length = item.length
        if length not in length_groups:
            length_groups[length] = []
        length_groups[length].append(item)
    
    strips = []
    penalty = 0
    
    # 按长度从大到小处理（长的先放，减少浪费）
    for length in sorted(length_groups.keys(), reverse=True):
        group_items = length_groups[length]
        current_strip = None
        
        for item in group_items:
            if current_strip is None or not current_strip.can_add(item):
                # 结算当前条
                if current_strip is not None and len(current_strip.items) > 0:
                    if not current_strip.is_valid():
                        penalty += PENALTY_VALUE
                    strips.append(current_strip)
                current_strip = Strip()
            
            current_strip.add_item(item)
        
        # 处理该长度组的最后一条
        if current_strip is not None and len(current_strip.items) > 0:
            if not current_strip.is_valid():
                penalty += PENALTY_VALUE
            strips.append(current_strip)
    
    total_length = sum(strip.strip_length for strip in strips)
    return total_length, strips, penalty


def decode_length_grouped(individual, items):
    """
    长度分组解码器：先按长度分组，组内再按宽度装箱
    
    核心思想：长度相近的板子放一起，减少长度方向浪费
    """
    # 按染色体顺序获取板子，但按长度分组处理
    ordered_items = [(idx, items[idx]) for idx in individual]
    
    # 按长度排序（相近的放一起）
    ordered_items.sort(key=lambda x: x[1].length)
    
    strips = []
    current_strip = Strip()
    penalty = 0
    
    for idx, item in ordered_items:
        # 检查是否能放入当前条
        if current_strip.can_add(item):
            # 检查长度差异，如果差异太大就不放
            if len(current_strip.items) == 0:
                current_strip.add_item(item)
            else:
                length_ratio = item.length / current_strip.strip_length
                # 允许长度在0.7-1.3倍范围内
                if 0.7 <= length_ratio <= 1.3:
                    current_strip.add_item(item)
                else:
                    # 长度差异太大，结算当前条
                    if len(current_strip.items) > 0:
                        if not current_strip.is_valid():
                            penalty += PENALTY_VALUE
                        strips.append(current_strip)
                    current_strip = Strip()
                    current_strip.add_item(item)
        else:
            # 宽度放不下了
            if len(current_strip.items) > 0:
                if not current_strip.is_valid():
                    penalty += PENALTY_VALUE
                strips.append(current_strip)
            current_strip = Strip()
            current_strip.add_item(item)
    
    if len(current_strip.items) > 0:
        if not current_strip.is_valid():
            penalty += PENALTY_VALUE
        strips.append(current_strip)
    
    total_length = sum(strip.strip_length for strip in strips)
    return total_length, strips, penalty


def decode_hybrid(individual, items):
    """
    优化解码器：尝试多种策略，选择最优
    """
    # 方法1: 简单顺序解码
    result1 = decode(individual, items)
    
    # 方法2: Best Fit解码
    result2 = decode_best_fit(individual, items)
    
    # 方法3: 同长度优先解码（关键优化）
    result3 = decode_same_length_first(individual, items)
    
    # 选择最优
    results = [result1, result2, result3]
    best = min(results, key=lambda r: r[0] + r[2])
    return best


def decode_width_first(individual, items):
    """
    宽度优先解码器：尽量填满宽度方向，同时考虑长度匹配
    
    核心思想：
    1. 对于每条strip，优先选择能最好填满剩余宽度的板子
    2. 同时惩罚长度差异过大的组合
    """
    # 按染色体顺序构建待处理队列
    queue = [items[idx] for idx in individual]
    used = [False] * len(queue)
    
    strips = []
    penalty = 0
    
    while not all(used):
        current_strip = Strip()
        
        # 找第一个未使用的板子开始
        for i, item in enumerate(queue):
            if not used[i]:
                current_strip.add_item(item)
                used[i] = True
                break
        
        # 贪心填充当前条
        improved = True
        while improved:
            improved = False
            best_idx = -1
            best_score = float('inf')
            
            remain_width = current_strip.get_remain_width()
            
            for i, item in enumerate(queue):
                if used[i] or item.width > remain_width:
                    continue
                
                # 计算放入这个板子的得分（越小越好）
                # 1. 宽度匹配：剩余宽度越小越好
                width_left = remain_width - item.width
                width_score = width_left if width_left >= MIN_CUT_GAP or width_left == 0 else 1000
                
                # 2. 长度匹配：与当前最长板差异越小越好
                length_diff = abs(item.length - current_strip.strip_length)
                length_score = length_diff
                
                # 3. 如果新板更长，会增加整体浪费
                if item.length > current_strip.strip_length:
                    extra_waste = (item.length - current_strip.strip_length) * current_strip.used_width
                    length_score += extra_waste * 0.5
                
                # 综合得分
                score = width_score * 2 + length_score
                
                # 如果能刚好填满或接近填满，大幅降低得分
                if width_left < MIN_CUT_GAP:
                    score -= 500
                
                if score < best_score:
                    best_score = score
                    best_idx = i
            
            if best_idx >= 0 and best_score < 2000:  # 有合适的板子
                current_strip.add_item(queue[best_idx])
                used[best_idx] = True
                improved = True
        
        # 检查约束
        if not current_strip.is_valid():
            penalty += PENALTY_VALUE
        
        strips.append(current_strip)
    
    total_length = sum(strip.strip_length for strip in strips)
    return total_length, strips, penalty


def decode_with_length_priority(individual, items):
    """
    带长度优先的解码器：在宽度允许的情况下，
    优先将长度相近的板子放在一起
    
    这个解码器会稍微调整顺序，使得同一条内的板子长度更接近
    """
    strips = []
    current_strip = Strip()
    penalty = 0
    pending = []  # 暂存无法放入当前条的板子
    
    for idx in individual:
        item = items[idx]
        
        if current_strip.can_add(item):
            # 如果当前条还是空的，直接放入
            if len(current_strip.items) == 0:
                current_strip.add_item(item)
            else:
                # 检查长度差异
                length_diff = abs(item.length - current_strip.strip_length)
                # 如果长度差异较小（比如不超过当前长度的50%），放入
                if length_diff <= current_strip.strip_length * 0.5:
                    current_strip.add_item(item)
                else:
                    # 长度差异太大，暂存
                    pending.append(item)
        else:
            # 放不下了，先尝试从pending中找能放的
            added_from_pending = True
            while added_from_pending and pending:
                added_from_pending = False
                for i, p_item in enumerate(pending):
                    if current_strip.can_add(p_item):
                        current_strip.add_item(p_item)
                        pending.pop(i)
                        added_from_pending = True
                        break
            
            # 结算当前条
            if len(current_strip.items) > 0:
                if not current_strip.is_valid():
                    penalty += PENALTY_VALUE
                strips.append(current_strip)
            
            # 开启新条
            current_strip = Strip()
            current_strip.add_item(item)
    
    # 处理pending中剩余的
    for item in pending:
        if current_strip.can_add(item):
            current_strip.add_item(item)
        else:
            if len(current_strip.items) > 0:
                if not current_strip.is_valid():
                    penalty += PENALTY_VALUE
                strips.append(current_strip)
            current_strip = Strip()
            current_strip.add_item(item)
    
    # 处理最后一条
    if len(current_strip.items) > 0:
        if not current_strip.is_valid():
            penalty += PENALTY_VALUE
        strips.append(current_strip)
    
    total_length = sum(strip.strip_length for strip in strips)
    
    return total_length, strips, penalty


def decode_stage_based(individual, items):
    """
    阶段式解码器：
    1. 先根据染色体顺序生成当前阶段的宽度组合
    2. 再像原始算法一样，为该组合计算一个阶段连续生产长度
    3. 用这一阶段一次性完成一批需求
    """
    remaining_counts = {}
    items_by_type = {}
    lengths_by_type = {}
    widths_by_type = {}

    for idx in individual:
        item = items[idx]
        remaining_counts[item.type_id] = remaining_counts.get(item.type_id, 0) + 1
        items_by_type.setdefault(item.type_id, []).append(item)
        lengths_by_type[item.type_id] = item.length
        widths_by_type[item.type_id] = item.width

    ordered_type_stream = [items[idx].type_id for idx in individual]
    consume_offsets = {type_id: 0 for type_id in remaining_counts}
    strips = []
    penalty = 0
    cursor = 0

    def fill_stage_combination():
        nonlocal cursor
        combination = {}
        used_width = 0
        visited_without_add = 0

        while visited_without_add < len(ordered_type_stream):
            type_id = ordered_type_stream[cursor % len(ordered_type_stream)]
            cursor += 1
            visited_without_add += 1

            if remaining_counts.get(type_id, 0) <= 0:
                continue

            item_width = widths_by_type[type_id]
            if used_width + item_width > PANEL_WIDTH:
                continue

            combination[type_id] = combination.get(type_id, 0) + 1
            used_width += item_width
            visited_without_add = 0

            # 如果剩余宽度已经小于最小产品宽度，就停止填充
            feasible_widths = [
                widths_by_type[t] for t, cnt in remaining_counts.items()
                if cnt > 0 and t in widths_by_type
            ]
            if feasible_widths:
                min_width = min(feasible_widths)
                remain = PANEL_WIDTH - used_width
                if remain < min_width:
                    break

        return combination, used_width

    while sum(remaining_counts.values()) > 0:
        combination, used_width = fill_stage_combination()
        if not combination:
            break

        cut_length = min(
            lengths_by_type[type_id] * math.ceil(remaining_counts[type_id] / combination[type_id])
            for type_id in combination
        )

        produced_counts = {
            type_id: min(
                remaining_counts[type_id],
                (cut_length // lengths_by_type[type_id]) * combination[type_id]
            )
            for type_id in combination
        }

        stage_strip = Strip()
        for type_id, count in combination.items():
            take = count
            start = consume_offsets[type_id]
            end = start + take
            stage_items = items_by_type[type_id][start:end]
            consume_offsets[type_id] = end
            for item in stage_items:
                stage_strip.add_item(item)

        stage_strip.strip_length = cut_length
        penalty += _strip_constraint_penalty(stage_strip)
        strips.append(stage_strip)

        for type_id, produced in produced_counts.items():
            remaining_counts[type_id] = max(0, remaining_counts[type_id] - produced)

    total_length = sum(strip.strip_length for strip in strips)
    return total_length, strips, penalty


def decode_pattern_guided(individual, items):
    """
    基于 pattern 库的解码器。
    先根据当前需求生成高价值组合，再用染色体顺序决定“优先满足哪一类”的 pattern。
    """
    type_specs = _get_type_specs(items)
    patterns = _build_pattern_library(type_specs)
    type_index_map = {spec[0]: idx for idx, spec in enumerate(type_specs)}

    ordered_items = [items[idx] for idx in individual]
    items_by_type = {spec[0]: [] for spec in type_specs}
    for item in ordered_items:
        items_by_type[item.type_id].append(item)

    remaining_counts = {type_id: len(type_items) for type_id, type_items in items_by_type.items()}
    consume_offsets = {type_id: 0 for type_id in items_by_type}
    strips = []
    penalty = 0
    anchor_cursor = 0

    def remaining_total():
        return sum(remaining_counts.values())

    while remaining_total() > 0:
        while anchor_cursor < len(ordered_items) and remaining_counts[ordered_items[anchor_cursor].type_id] == 0:
            anchor_cursor += 1
        if anchor_cursor >= len(ordered_items):
            break

        anchor_type = ordered_items[anchor_cursor].type_id
        feasible_patterns = []
        for pattern in patterns:
            counts = pattern["counts"]
            anchor_count = counts[type_index_map[anchor_type]]
            if anchor_count <= 0:
                continue
            if any(
                counts[type_index_map[type_id]] > remaining_counts[type_id]
                for type_id in remaining_counts
            ):
                continue

            score = (
                pattern["savings"] * 1000.0
                + pattern["efficiency"] * 100.0
                - pattern["waste_width"] * 0.2
                + anchor_count * 0.5
            )
            feasible_patterns.append((score, pattern))

        if feasible_patterns:
            feasible_patterns.sort(key=lambda pair: pair[0], reverse=True)
            _, best_pattern = feasible_patterns[:PATTERN_TOP_CANDIDATES][0]
        else:
            # 保底：给 anchor_type 构造一个纯类型 strip
            anchor_width = type_specs[type_index_map[anchor_type]][1]
            max_count = min(
                remaining_counts[anchor_type],
                PANEL_WIDTH // anchor_width,
            )
            counts = [0] * len(type_specs)
            counts[type_index_map[anchor_type]] = max_count
            best_pattern = {
                "counts": tuple(counts),
                "used_width": max_count * anchor_width,
                "strip_length": type_specs[type_index_map[anchor_type]][2],
                "efficiency": 0.0,
                "savings": 0.0,
                "waste_width": PANEL_WIDTH - max_count * anchor_width,
            }

        strip = Strip()
        for type_id, type_items in items_by_type.items():
            type_pos = type_index_map[type_id]
            need_count = best_pattern["counts"][type_pos]
            if need_count <= 0:
                continue

            start = consume_offsets[type_id]
            end = start + need_count
            chosen_items = type_items[start:end]
            consume_offsets[type_id] = end
            remaining_counts[type_id] -= need_count

            for item in chosen_items:
                strip.add_item(item)

        penalty += _strip_constraint_penalty(strip)
        strips.append(strip)

    total_length = sum(strip.strip_length for strip in strips)
    return total_length, strips, penalty


def decode_by_mode(individual, items, mode=None):
    """
    按配置选择解码策略。
    """
    decoder_mode = (mode or DECODER_MODE).lower()

    if decoder_mode == 'simple':
        return decode(individual, items)
    if decoder_mode == 'best_fit':
        return decode_best_fit(individual, items)
    if decoder_mode == 'length_priority':
        return decode_with_length_priority(individual, items)
    if decoder_mode == 'stage_based':
        return decode_stage_based(individual, items)
    if decoder_mode == 'pattern_guided':
        return decode_pattern_guided(individual, items)
    if decoder_mode == 'hybrid':
        return decode_hybrid(individual, items)

    raise ValueError(f"未知解码模式: {decoder_mode}")


def calculate_fitness(individual, items, decoder_mode=None):
    """
    计算适应度（越小越好）
    
    参数:
        individual: list of int，染色体
        items: list of Item，所有小板列表
        decoder_mode: str，解码模式
    
    返回:
        fitness: float，适应度值（总长度 + 惩罚）
    """
    total_length, strips, penalty = decode_by_mode(individual, items, decoder_mode)
    fitness = total_length + penalty
    return fitness


def calculate_efficiency(total_length, items, scale_factor=1):
    """
    计算材料利用率
    
    参数:
        total_length: 总消耗长度
        items: 所有小板列表
        scale_factor: 缩放因子（用于还原真实数量）
    
    返回:
        efficiency: float，利用率百分比
    """
    total_area_used = sum(item.width * item.length for item in items) * scale_factor
    total_area_available = PANEL_WIDTH * total_length * scale_factor
    
    if total_area_available == 0:
        return 0
    
    efficiency = 100 * total_area_used / total_area_available
    return efficiency


def get_cutting_plan(strips, type_info):
    """
    将解码后的strips转换为易读的切割方案
    
    参数:
        strips: list of Strip
        type_info: DataFrame，产品类型信息
    
    返回:
        plan: list of dict，每个字典表示一条的切割信息
    """
    plan = []
    accumulated_length = 0
    
    for i, strip in enumerate(strips):
        accumulated_length += strip.strip_length
        
        # 统计该条中各类型的数量
        type_counts = {}
        for item in strip.items:
            type_id = item.type_id
            if type_id not in type_counts:
                type_counts[type_id] = 0
            type_counts[type_id] += 1
        
        strip_info = {
            'strip_id': i + 1,
            'strip_length': strip.strip_length,
            'accumulated_length': accumulated_length,
            'used_width': strip.used_width,
            'waste_width': PANEL_WIDTH - strip.used_width,
            'type_counts': type_counts,
            'items': strip.items
        }
        plan.append(strip_info)
    
    return plan


def merge_same_pattern_strips(strips):
    """
    合并相同切割模式的连续条
    
    如果连续多条的宽度组合相同，可以合并计算
    返回合并后的strips和对应的重复次数
    """
    if not strips:
        return [], []
    
    merged_strips = []
    repeat_counts = []
    
    current_pattern = None
    current_count = 0
    current_strip = None
    
    for strip in strips:
        # 提取模式：按类型统计宽度组合
        pattern = tuple(sorted([item.type_id for item in strip.items]))
        
        if pattern == current_pattern and strip.strip_length == current_strip.strip_length:
            current_count += 1
        else:
            if current_strip is not None:
                merged_strips.append(current_strip)
                repeat_counts.append(current_count)
            current_pattern = pattern
            current_strip = strip
            current_count = 1
    
    # 处理最后一组
    if current_strip is not None:
        merged_strips.append(current_strip)
        repeat_counts.append(current_count)
    
    return merged_strips, repeat_counts


if __name__ == "__main__":
    # 测试解码器
    from core.data_loader import load_demand_from_excel, expand_demand, Item
    import random
    
    # 加载数据
    demand = load_demand_from_excel(sheet_num=1)
    items, type_info = expand_demand(demand)
    
    print(f"总共 {len(items)} 个小板")
    
    # 创建随机染色体
    individual = list(range(len(items)))
    random.shuffle(individual)
    
    # 解码
    total_length, strips, penalty = decode_by_mode(individual, items)
    efficiency = calculate_efficiency(total_length, items)
    
    print(f"\n随机方案结果:")
    print(f"总长度: {total_length}")
    print(f"惩罚值: {penalty}")
    print(f"切割条数: {len(strips)}")
    print(f"利用率: {efficiency:.2f}%")
    
    # 打印前几条的详情
    print("\n前3条详情:")
    for i, strip in enumerate(strips[:3]):
        print(f"  Strip {i+1}: {strip}")
