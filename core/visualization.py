# -*- coding: utf-8 -*-
"""
可视化模块 - 切割方案可视化和进化过程可视化
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from core.config import PANEL_WIDTH

# 图片显示中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def plot_cutting_plan(strips, items, type_info, efficiency, save_path=None, show=True):
    """
    绘制切割方案图
    
    参数:
        strips: list of Strip，切割方案
        items: list of Item，所有小板
        type_info: DataFrame，产品类型信息
        efficiency: float，材料利用率
        save_path: str，保存路径（可选）
    """
    # 计算总长度
    total_length = sum(strip.strip_length for strip in strips)
    
    # 设置画布大小
    fig_width = 14
    fig_height = max(8, len(strips) * 0.5)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # 缩放因子
    scale_x = fig_width * 50 / total_length if total_length > 0 else 1
    scale_y = fig_height * 50 / PANEL_WIDTH
    
    # 颜色映射
    num_types = len(type_info) if type_info is not None else 10
    colors = plt.cm.Set3(np.linspace(0, 1, num_types))
    
    # 绘制大板背景
    y_offset = 0
    
    for strip_idx, strip in enumerate(strips):
        # 绘制该条的背景（灰色表示原材料）
        bg_rect = patches.Rectangle(
            (0, y_offset),
            strip.strip_length * scale_x,
            PANEL_WIDTH * scale_y,
            linewidth=1,
            edgecolor='black',
            facecolor='lightgray',
            alpha=0.3
        )
        ax.add_patch(bg_rect)
        
        # 绘制该条中的小板
        x_offset = 0
        for item in strip.items:
            # 小板颜色根据类型
            color = colors[item.type_id % len(colors)]
            
            rect = patches.Rectangle(
                (x_offset, y_offset),
                item.length * scale_x,
                item.width * scale_y,
                linewidth=0.5,
                edgecolor='black',
                facecolor=color
            )
            ax.add_patch(rect)
            
            # 添加标签（如果空间足够）
            if item.length * scale_x > 20 and item.width * scale_y > 15:
                ax.text(
                    x_offset + item.length * scale_x / 2,
                    y_offset + item.width * scale_y / 2,
                    f'T{item.type_id + 1}',
                    ha='center', va='center',
                    fontsize=7, color='black'
                )
            
            x_offset += item.length * scale_x
        
        # 条号标签
        ax.text(
            -10, y_offset + PANEL_WIDTH * scale_y / 2,
            f'#{strip_idx + 1}',
            ha='right', va='center',
            fontsize=9, fontweight='bold'
        )
        
        # 长度标签
        ax.text(
            strip.strip_length * scale_x + 5,
            y_offset + PANEL_WIDTH * scale_y / 2,
            f'L={strip.strip_length:.0f}',
            ha='left', va='center',
            fontsize=8
        )
        
        y_offset += PANEL_WIDTH * scale_y + 5
    
    # 设置坐标轴
    ax.set_xlim(-30, total_length * scale_x + 80)
    ax.set_ylim(-10, y_offset + 10)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 标题
    ax.set_title(
        f'切割方案 - 总长度: {total_length:.0f}mm, '
        f'切割条数: {len(strips)}, '
        f'材料利用率: {efficiency:.2f}%',
        fontsize=12, fontweight='bold'
    )
    
    # 添加图例
    if type_info is not None:
        legend_patches = []
        for i in range(len(type_info)):
            patch = patches.Patch(
                color=colors[i],
                label=f'类型{i+1}: {type_info["Width"].iloc[i]}x{type_info["Length"].iloc[i]}'
            )
            legend_patches.append(patch)
        ax.legend(handles=legend_patches, loc='upper right', fontsize=8)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"切割方案图已保存至: {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_evolution_history(history, save_path=None, show=True):
    """
    绘制进化历史曲线
    
    参数:
        history: dict，进化历史记录
        save_path: str，保存路径（可选）
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    generations = range(1, len(history['best_fitness']) + 1)
    
    # 最优适应度曲线
    axes[0].plot(generations, history['best_fitness'], 'b-', linewidth=2, label='最优适应度')
    axes[0].set_xlabel('迭代代数')
    axes[0].set_ylabel('适应度值（总长度）')
    axes[0].set_title('最优适应度进化曲线')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    
    # 平均适应度曲线
    axes[1].plot(generations, history['avg_fitness'], 'r-', linewidth=2, label='平均适应度')
    axes[1].plot(generations, history['best_fitness'], 'b--', linewidth=1, label='最优适应度')
    axes[1].set_xlabel('迭代代数')
    axes[1].set_ylabel('适应度值')
    axes[1].set_title('种群适应度进化曲线')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"进化曲线图已保存至: {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_strip_details(strips, type_info, save_path=None, show=True):
    """
    绘制每条切割带的详细信息柱状图
    
    参数:
        strips: list of Strip
        type_info: DataFrame
        save_path: str
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    strip_nums = range(1, len(strips) + 1)
    lengths = [strip.strip_length for strip in strips]
    widths = [strip.used_width for strip in strips]
    waste_widths = [PANEL_WIDTH - strip.used_width for strip in strips]
    
    # 长度柱状图
    axes[0].bar(strip_nums, lengths, color='steelblue', edgecolor='black')
    axes[0].axhline(y=np.mean(lengths), color='red', linestyle='--', label=f'平均长度: {np.mean(lengths):.0f}')
    axes[0].set_xlabel('切割条编号')
    axes[0].set_ylabel('长度 (mm)')
    axes[0].set_title('各切割条长度分布')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # 宽度利用柱状图
    axes[1].bar(strip_nums, widths, color='green', edgecolor='black', label='已使用宽度')
    axes[1].bar(strip_nums, waste_widths, bottom=widths, color='red', edgecolor='black', alpha=0.5, label='浪费宽度')
    axes[1].axhline(y=PANEL_WIDTH, color='black', linestyle='-', linewidth=2)
    axes[1].set_xlabel('切割条编号')
    axes[1].set_ylabel('宽度 (mm)')
    axes[1].set_title('各切割条宽度利用情况')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"详细信息图已保存至: {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_compact_cutting_plan(strips, repeat_counts, efficiency, save_path=None, show=True):
    """
    以原始算法 result.png 的风格绘制压缩排版图。
    每个 strip 模式按重复次数压缩成一个阶段，横向表示累计长度，纵向表示板宽分配。
    """
    total_length = sum(strip.strip_length * count for strip, count in zip(strips, repeat_counts))
    if total_length <= 0:
        return

    figure_x = 200.0
    figure_y = 100.0
    scale_x = figure_x / total_length
    scale_y = figure_y / PANEL_WIDTH

    fig, ax = plt.subplots(figsize=(12, 8))

    # 整张母板背景
    bg = patches.Rectangle(
        (0, 0),
        total_length * scale_x,
        PANEL_WIDTH * scale_y,
        facecolor='lightgray',
        edgecolor='black',
        linewidth=1.5,
        alpha=0.8
    )
    ax.add_patch(bg)

    current_x = 0.0
    for strip, repeat_count in zip(strips, repeat_counts):
        stage_length = strip.strip_length * repeat_count
        stage_width = stage_length * scale_x

        # 阶段边界
        stage_bg = patches.Rectangle(
            (current_x, 0),
            stage_width,
            PANEL_WIDTH * scale_y,
            facecolor='lightgray',
            edgecolor='black',
            linewidth=1.0,
            alpha=0.15
        )
        ax.add_patch(stage_bg)

        y_cursor = 0.0
        grouped_items = {}
        item_order = []
        for item in strip.items:
            key = (item.type_id, item.width, item.length)
            if key not in grouped_items:
                grouped_items[key] = 0
                item_order.append(key)
            grouped_items[key] += 1

        for type_id, item_width, item_length in sorted(item_order):
            lane_count = grouped_items[(type_id, item_width, item_length)]
            lane_length = item_length * repeat_count * scale_x

            for _ in range(lane_count):
                rect = patches.Rectangle(
                    (current_x, y_cursor),
                    lane_length,
                    item_width * scale_y,
                    facecolor='royalblue',
                    edgecolor='red',
                    linewidth=1.2
                )
                ax.add_patch(rect)

                if lane_length > 6 and item_width * scale_y > 6:
                    ax.text(
                        current_x + lane_length / 2,
                        y_cursor + item_width * scale_y / 2,
                        f'item:{type_id + 1}\nnum:{repeat_count}',
                        ha='center',
                        va='center',
                        fontsize=10,
                        color='white'
                    )

                if lane_length > 10:
                    ax.text(
                        current_x + lane_length / 2,
                        max(0.5, y_cursor - 0.8),
                        f'长度: {int(item_length * repeat_count)}',
                        ha='center',
                        va='top',
                        fontsize=8,
                        color='black'
                    )

                if item_width * scale_y > 8:
                    ax.text(
                        max(0.5, current_x - 0.8),
                        y_cursor + item_width * scale_y / 2,
                        f'宽度: {int(item_width)}',
                        ha='right',
                        va='center',
                        fontsize=8,
                        color='black',
                        rotation='vertical'
                    )

                y_cursor += item_width * scale_y

        current_x += stage_width

    ax.set_xlim(0, total_length * scale_x + 2)
    ax.set_ylim(0, PANEL_WIDTH * scale_y + 2)
    ax.axis('off')
    ax.set_title(f'面积利用率: {efficiency:.2f}%', fontsize=14)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"压缩排版图已保存至: {save_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def _collect_stage_groups(strip):
    """
    按出现顺序统计一个阶段中的宽度组合。
    返回值中的每个元素表示一条纵向条带。
    """
    groups = []
    group_index = {}

    for item in strip.items:
        key = (item.type_id, item.width, item.length)
        if key not in group_index:
            group_index[key] = len(groups)
            groups.append(
                {
                    "type_id": item.type_id,
                    "width": item.width,
                    "length": item.length,
                    "lane_count": 0,
                }
            )
        groups[group_index[key]]["lane_count"] += 1

    return groups


def _format_stage_combination(stage_groups):
    """
    生成阶段顶部显示的宽度组合文字。
    """
    combo_parts = [f"T{group['type_id'] + 1}×{group['lane_count']}" for group in stage_groups]

    width_parts = []
    for group in stage_groups:
        width_parts.extend([str(int(group["width"]))] * group["lane_count"])

    used_width = sum(group["width"] * group["lane_count"] for group in stage_groups)
    return " + ".join(combo_parts), " + ".join(width_parts), used_width


def plot_stage_based_cutting_plan(strips, efficiency, save_path=None, show=True):
    """
    以接近原始 result.png 的风格绘制 stage_based 解码结果。

    横向表示阶段累计长度，纵向表示母板宽度 1250mm。
    每个阶段内部按宽度组合上下堆叠，矩形长度表示该条带实际消耗长度，
    灰色尾部表示该阶段内因为横切统一长度产生的损耗。
    """
    total_length = sum(strip.strip_length for strip in strips)
    if total_length <= 0:
        return

    figure_x = 200.0
    figure_y = 100.0
    scale_x = figure_x / total_length
    scale_y = figure_y / PANEL_WIDTH

    fig, ax = plt.subplots(figsize=(12, 8))

    sheet = patches.Rectangle(
        (0, 0),
        total_length * scale_x,
        PANEL_WIDTH * scale_y,
        facecolor="lightgray",
        edgecolor="black",
        linewidth=1.5,
        alpha=0.9,
    )
    ax.add_patch(sheet)

    current_x = 0.0
    max_stage_label_y = PANEL_WIDTH * scale_y
    summary_lines = []

    for stage_index, strip in enumerate(strips, start=1):
        stage_length_scaled = strip.strip_length * scale_x
        stage_groups = _collect_stage_groups(strip)
        combo_text, width_text, used_width = _format_stage_combination(stage_groups)
        summary_lines.append(
            f"阶段{stage_index}: {combo_text}   宽度组合: {width_text} = {int(used_width)}"
        )

        stage_outline = patches.Rectangle(
            (current_x, 0),
            stage_length_scaled,
            PANEL_WIDTH * scale_y,
            facecolor="none",
            edgecolor="gray",
            linewidth=1.0,
            alpha=0.6,
        )
        ax.add_patch(stage_outline)

        y_cursor = 0.0
        for group in stage_groups:
            item_width = group["width"]
            item_length = group["length"]
            lane_piece_count = max(1, strip.strip_length // item_length)
            lane_length = item_length * lane_piece_count
            lane_length_scaled = lane_length * scale_x

            for _ in range(group["lane_count"]):
                rect = patches.Rectangle(
                    (current_x, y_cursor),
                    lane_length_scaled,
                    item_width * scale_y,
                    facecolor="royalblue",
                    edgecolor="red",
                    linewidth=1.2,
                )
                ax.add_patch(rect)

                if lane_length_scaled > 8 and item_width * scale_y > 8:
                    ax.text(
                        current_x + lane_length_scaled / 2,
                        y_cursor + item_width * scale_y / 2,
                        f"item:{group['type_id'] + 1}\nnum:{lane_piece_count}",
                        ha="center",
                        va="center",
                        color="white",
                        fontsize=9,
                    )

                if lane_length_scaled > 10:
                    ax.text(
                        current_x + lane_length_scaled / 2,
                        max(0.6, y_cursor - 0.8),
                        f"长度: {int(lane_length)}",
                        ha="center",
                        va="top",
                        color="black",
                        fontsize=8,
                    )

                if item_width * scale_y > 7:
                    ax.text(
                        max(0.4, current_x - 0.8),
                        y_cursor + item_width * scale_y / 2,
                        f"宽度: {int(item_width)}",
                        ha="right",
                        va="center",
                        color="black",
                        fontsize=8,
                        rotation="vertical",
                    )

                y_cursor += item_width * scale_y

        stage_label_y = PANEL_WIDTH * scale_y + 1.6
        max_stage_label_y = max(max_stage_label_y, stage_label_y)
        ax.text(
            current_x + stage_length_scaled / 2,
            stage_label_y,
            f"阶段{stage_index}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="black",
        )

        current_x += stage_length_scaled

    summary_y = max_stage_label_y + 3.0
    ax.text(
        0.0,
        summary_y,
        "\n".join(summary_lines),
        ha="left",
        va="bottom",
        fontsize=8,
        color="black",
        bbox={
            "facecolor": "white",
            "edgecolor": "lightgray",
            "alpha": 0.9,
            "boxstyle": "round,pad=0.3",
        },
    )

    ax.set_xlim(-2, total_length * scale_x + 2)
    ax.set_ylim(-2, summary_y + 10)
    ax.axis("off")
    ax.set_title(f"面积利用率: {efficiency:.2f}%", fontsize=14)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"阶段排版图已保存至: {save_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def print_solution_summary(solution, type_info):
    """
    打印解决方案摘要
    
    参数:
        solution: dict，解决方案
        type_info: DataFrame，产品类型信息
    """
    print("=" * 60)
    print("                   切割方案摘要")
    print("=" * 60)
    print(f"总切割长度: {solution['total_length']:.2f} mm")
    print(f"材料利用率: {solution['efficiency']:.2f}%")
    print(f"切割条数: {solution['num_strips']}")
    print(f"惩罚值: {solution['penalty']}")
    print("-" * 60)
    
    print("\n各条详情:")
    print("-" * 60)
    
    accumulated_length = 0
    for i, strip in enumerate(solution['strips']):
        accumulated_length += strip.strip_length
        
        # 统计各类型数量
        type_counts = {}
        for item in strip.items:
            type_id = item.type_id
            if type_id not in type_counts:
                type_counts[type_id] = 0
            type_counts[type_id] += 1
        
        type_str = ", ".join([f"T{k+1}:{v}" for k, v in sorted(type_counts.items())])
        
        print(f"条#{i+1}: 长度={strip.strip_length:.0f}mm, "
              f"宽度={strip.used_width}mm, "
              f"累计长度={accumulated_length:.0f}mm")
        print(f"       包含: {type_str}")
    
    print("=" * 60)


if __name__ == "__main__":
    # 测试可视化
    from core.data_loader import load_demand_from_excel, expand_demand
    from core.decoder import decode
    import random
    
    # 加载数据
    demand = load_demand_from_excel(sheet_num=1)
    items, type_info = expand_demand(demand)
    
    # 创建随机方案
    individual = list(range(len(items)))
    random.shuffle(individual)
    
    total_length, strips, penalty = decode(individual, items)
    efficiency = 100 * sum(item.width * item.length for item in items) / (PANEL_WIDTH * total_length)
    
    print(f"测试方案: 长度={total_length}, 利用率={efficiency:.2f}%")
    
    # 绘制
    plot_cutting_plan(strips[:10], items, type_info, efficiency)  # 只画前10条
