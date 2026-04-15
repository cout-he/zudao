# -*- coding: utf-8 -*-
"""
可视化模块 - 切割方案可视化和进化过程可视化
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from core.config import PANEL_WIDTH, SCALE_FACTOR

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
    total_length = sum(strip.strip_length * count * SCALE_FACTOR for strip, count in zip(strips, repeat_counts))
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


def _draw_stage_zoom_card(ax, stage_info, card_x, card_y, card_width, card_height, color_map):
    title_height = 3.8
    inner_pad = 1.0
    inner_x = card_x + inner_pad
    inner_y = card_y + inner_pad
    inner_w = card_width - inner_pad * 2
    inner_h = card_height - inner_pad * 2 - title_height

    card = patches.FancyBboxPatch(
        (card_x, card_y),
        card_width,
        card_height,
        boxstyle="round,pad=0.35",
        linewidth=1.0,
        edgecolor="#9aa4b2",
        facecolor="white",
        alpha=0.97,
    )
    ax.add_patch(card)

    title_text = stage_info.get("title", f"阶段{stage_info['stage_index']} 放大")
    ax.text(
        card_x + card_width / 2,
        card_y + card_height - 1.1,
        title_text,
        ha="center",
        va="top",
        fontsize=8,
        fontweight="bold",
        color="#2f3b52",
    )

    inner_bg = patches.Rectangle(
        (inner_x, inner_y),
        inner_w,
        inner_h,
        facecolor="#f5f7fa",
        edgecolor="#c5cbd3",
        linewidth=0.8,
    )
    ax.add_patch(inner_bg)

    y_cursor = inner_y
    for group in stage_info["stage_groups"]:
        lane_height = inner_h * group["width"] / PANEL_WIDTH
        color = color_map[group["type_id"]]
        group_start_y = y_cursor
        for _ in range(group["lane_count"]):
            lane_rect = patches.Rectangle(
                (inner_x, y_cursor),
                inner_w,
                lane_height,
                facecolor=color,
                edgecolor="white",
                linewidth=0.7,
            )
            ax.add_patch(lane_rect)
            y_cursor += lane_height

        group_total_height = y_cursor - group_start_y
        if group_total_height >= 2.3:
            display_quantity = group.get("display_quantity", group["lane_count"])
            ax.text(
                inner_x + inner_w / 2,
                group_start_y + group_total_height / 2,
                f"T{group['type_id'] + 1}\n数量:{display_quantity}",
                ha="center",
                va="center",
                fontsize=6.8,
                color="white",
                fontweight="bold",
            )

    remain_width = max(0, PANEL_WIDTH - stage_info["used_width"])
    remain_height = inner_y + inner_h - y_cursor
    if remain_height > 0.3:
        remain_rect = patches.Rectangle(
            (inner_x, y_cursor),
            inner_w,
            remain_height,
            facecolor="#d9dde3",
            edgecolor="#7f8c8d",
            linewidth=0.8,
            hatch="///",
            alpha=0.95,
        )
        ax.add_patch(remain_rect)
        ax.text(
            inner_x + inner_w / 2,
            y_cursor + remain_height / 2,
            f"余宽 {int(remain_width)}",
            ha="center",
            va="center",
            fontsize=6.3,
            color="#444",
        )

    ax.annotate(
        "",
        xy=stage_info["anchor"],
        xytext=(card_x, card_y + card_height / 2),
        arrowprops={
            "arrowstyle": "->",
            "color": "#7f8c8d",
            "linewidth": 1.0,
            "shrinkA": 2,
            "shrinkB": 3,
            "connectionstyle": "arc3,rad=0.12",
        },
    )


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


def plot_stage_based_cutting_plan(strips, efficiency, save_path=None, show=True):
    """
    绘制 stage_based 解码结果。
    横向表示阶段累计长度，纵向表示母板宽度 1250mm。
    彩色矩形为实际切割区域，灰色斜线尾部表示阶段统一长度带来的余料。
    对较窄阶段额外绘制右侧放大卡片，提升可读性。
    """
    total_length = sum(strip.strip_length for strip in strips)
    if total_length <= 0:
        return

    figure_x = 205.0
    figure_y = 100.0
    scale_x = figure_x / total_length
    scale_y = figure_y / PANEL_WIDTH

    fig, ax = plt.subplots(figsize=(16, 9))

    type_ids = sorted({item.type_id for strip in strips for item in strip.items})
    palette = plt.cm.tab20(np.linspace(0.08, 0.92, max(1, len(type_ids))))
    color_map = {type_id: palette[i % len(palette)] for i, type_id in enumerate(type_ids)}

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
    tail_annotations = []
    stage_zoom_cards = []
    narrow_stage_threshold = 12.0
    max_tail_annotations = 5
    max_zoom_cards = 3

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
        largest_tail = None

        for group in stage_groups:
            item_width = group["width"]
            item_length = group["length"]
            lane_piece_count = max(1, strip.strip_length // item_length)
            lane_length = item_length * lane_piece_count
            lane_length_scaled = lane_length * scale_x
            waste_length = max(0, strip.strip_length - lane_length)
            waste_length_scaled = waste_length * scale_x
            color = color_map[group["type_id"]]
            group_start_y = y_cursor

            for _ in range(group["lane_count"]):
                rect = patches.Rectangle(
                    (current_x, y_cursor),
                    lane_length_scaled,
                    item_width * scale_y,
                    facecolor=color,
                    edgecolor="red",
                    linewidth=1.2,
                )
                ax.add_patch(rect)

                if waste_length_scaled > 0:
                    waste_rect = patches.Rectangle(
                        (current_x + lane_length_scaled, y_cursor),
                        waste_length_scaled,
                        item_width * scale_y,
                        facecolor="#d9dde3",
                        edgecolor="#7f8c8d",
                        linewidth=0.9,
                        hatch="///",
                        alpha=0.95,
                    )
                    ax.add_patch(waste_rect)

                if stage_length_scaled >= narrow_stage_threshold and lane_length_scaled > 8 and item_width * scale_y > 8:
                    ax.text(
                        current_x + lane_length_scaled / 2,
                        y_cursor + item_width * scale_y / 2,
                        f"T{group['type_id'] + 1}\n数量:{lane_piece_count}",
                        ha="center",
                        va="center",
                        color="white",
                        fontsize=9,
                        fontweight="bold",
                    )

                if stage_length_scaled >= narrow_stage_threshold and lane_length_scaled > 10:
                    ax.text(
                        current_x + lane_length_scaled / 2,
                        max(0.6, y_cursor - 0.8),
                        f"长度: {int(lane_length)}",
                        ha="center",
                        va="top",
                        color="black",
                        fontsize=8,
                    )

                if stage_length_scaled >= narrow_stage_threshold and item_width * scale_y > 7:
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

            if waste_length > 0:
                candidate_tail = {
                    "waste_length": waste_length,
                    "xy": (
                        current_x + lane_length_scaled + waste_length_scaled / 2,
                        group_start_y + group["lane_count"] * item_width * scale_y / 2,
                    ),
                    "xytext": (
                        current_x + stage_length_scaled + 1.4,
                        min(
                            PANEL_WIDTH * scale_y + 5.8,
                            group_start_y + group["lane_count"] * item_width * scale_y + 2.0,
                        ),
                    ),
                }
                if largest_tail is None or candidate_tail["waste_length"] > largest_tail["waste_length"]:
                    largest_tail = candidate_tail

        if largest_tail is not None:
            tail_annotations.append(largest_tail)

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

        if stage_length_scaled < narrow_stage_threshold:
            stage_zoom_cards.append(
                {
                    "stage_index": stage_index,
                    "stage_groups": [
                        {
                            **group,
                            "display_quantity": max(1, strip.strip_length // group["length"]) * group["lane_count"],
                        }
                        for group in stage_groups
                    ],
                    "used_width": used_width,
                    "stage_width": stage_length_scaled,
                    "lane_total": sum(group["lane_count"] for group in stage_groups),
                    "anchor": (
                        current_x + stage_length_scaled / 2,
                        PANEL_WIDTH * scale_y * 0.78,
                    ),
                }
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

    tail_annotations = sorted(
        tail_annotations,
        key=lambda item: item["waste_length"],
        reverse=True,
    )[:max_tail_annotations]

    for annotation in tail_annotations:
        ax.annotate(
            f"余料 {int(annotation['waste_length'])}",
            xy=annotation["xy"],
            xytext=annotation["xytext"],
            fontsize=7,
            color="#555",
            ha="left",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "#c9cfd6",
                "alpha": 0.95,
            },
            arrowprops={
                "arrowstyle": "->",
                "color": "#7f8c8d",
                "linewidth": 0.9,
                "shrinkA": 3,
                "shrinkB": 2,
            },
        )

    stage_zoom_cards = sorted(
        stage_zoom_cards,
        key=lambda item: (item["stage_width"], item["lane_total"], item["stage_index"]),
    )[:max_zoom_cards]

    right_margin = 4.0
    if stage_zoom_cards:
        card_width = 22.0
        card_height = 27.0
        card_gap = 3.0
        card_x = total_length * scale_x + 6.0
        card_y = PANEL_WIDTH * scale_y - card_height
        for stage_info in stage_zoom_cards:
            _draw_stage_zoom_card(
                ax,
                stage_info,
                card_x,
                card_y,
                card_width,
                card_height,
                color_map,
            )
            card_y -= card_height + card_gap
        right_margin = card_width + 10.0

    legend_handles = [
        patches.Patch(
            facecolor=color_map[type_id],
            edgecolor="white",
            label=f"T{type_id + 1}",
        )
        for type_id in type_ids
    ]
    legend_handles.append(
        patches.Patch(
            facecolor="#d9dde3",
            edgecolor="#7f8c8d",
            hatch="///",
            label="阶段尾部余料",
        )
    )
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        bbox_to_anchor=(1.0, 0.98),
        fontsize=8,
        frameon=True,
    )

    ax.set_xlim(-2, total_length * scale_x + right_margin)
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


def plot_compact_cutting_plan(strips, repeat_counts, efficiency, save_path=None, show=True):
    """
    绘制 simple / best_fit 等解码模式的压缩排布图。
    每个 strip 模式按重复次数压缩成一个阶段，横向表示累计长度，纵向表示板宽分配。
    对过窄阶段增加右侧放大卡片，并用箭头标注条带尾部余料。
    """
    total_length = sum(strip.strip_length * count for strip, count in zip(strips, repeat_counts))
    if total_length <= 0:
        return

    figure_x = 205.0
    figure_y = 100.0
    scale_x = figure_x / total_length
    scale_y = figure_y / PANEL_WIDTH

    fig, ax = plt.subplots(figsize=(16, 9))

    type_ids = sorted({item.type_id for strip in strips for item in strip.items})
    palette = plt.cm.tab20(np.linspace(0.08, 0.92, max(1, len(type_ids))))
    color_map = {type_id: palette[i % len(palette)] for i, type_id in enumerate(type_ids)}

    bg = patches.Rectangle(
        (0, 0),
        total_length * scale_x,
        PANEL_WIDTH * scale_y,
        facecolor="lightgray",
        edgecolor="black",
        linewidth=1.5,
        alpha=0.85,
    )
    ax.add_patch(bg)

    current_x = 0.0
    max_label_y = PANEL_WIDTH * scale_y
    summary_lines = []
    tail_annotations = []
    zoom_cards = []
    narrow_stage_threshold = 12.0
    max_summary_lines = 4 if len(strips) > 12 else (6 if len(strips) > 8 else 10)
    max_tail_annotations = 3 if len(strips) > 8 else 5
    max_zoom_cards = 3

    for stage_index, (strip, repeat_count) in enumerate(zip(strips, repeat_counts), start=1):
        actual_repeat_count = repeat_count * SCALE_FACTOR
        stage_length = strip.strip_length * actual_repeat_count
        stage_width = stage_length * scale_x
        stage_groups = _collect_stage_groups(strip)
        combo_text, width_text, used_width = _format_stage_combination(stage_groups)
        summary_lines.append(
            f"模式{stage_index}: {combo_text}   宽度组合: {width_text} = {int(used_width)}   重复: {int(actual_repeat_count)}"
        )

        stage_bg = patches.Rectangle(
            (current_x, 0),
            stage_width,
            PANEL_WIDTH * scale_y,
            facecolor="none",
            edgecolor="gray",
            linewidth=1.0,
            alpha=0.6,
        )
        ax.add_patch(stage_bg)

        y_cursor = 0.0
        largest_tail = None
        for group in stage_groups:
            type_id = group["type_id"]
            item_width = group["width"]
            item_length = group["length"]
            lane_count = group["lane_count"]
            useful_length = item_length * actual_repeat_count
            useful_length_scaled = useful_length * scale_x
            waste_length = max(0, stage_length - useful_length)
            waste_length_scaled = waste_length * scale_x
            color = color_map[type_id]
            group_start_y = y_cursor

            for _ in range(lane_count):
                rect = patches.Rectangle(
                    (current_x, y_cursor),
                    useful_length_scaled,
                    item_width * scale_y,
                    facecolor=color,
                    edgecolor="red",
                    linewidth=1.2,
                )
                ax.add_patch(rect)

                if waste_length_scaled > 0:
                    waste_rect = patches.Rectangle(
                        (current_x + useful_length_scaled, y_cursor),
                        waste_length_scaled,
                        item_width * scale_y,
                        facecolor="#d9dde3",
                        edgecolor="#7f8c8d",
                        linewidth=0.9,
                        hatch="///",
                        alpha=0.95,
                    )
                    ax.add_patch(waste_rect)

                if stage_width >= narrow_stage_threshold and useful_length_scaled > 6 and item_width * scale_y > 6:
                    ax.text(
                        current_x + useful_length_scaled / 2,
                        y_cursor + item_width * scale_y / 2,
                        f"T{type_id + 1}\n数量:{actual_repeat_count}",
                        ha="center",
                        va="center",
                        fontsize=9,
                        color="white",
                        fontweight="bold",
                    )

                if stage_width >= narrow_stage_threshold and useful_length_scaled > 10:
                    ax.text(
                        current_x + useful_length_scaled / 2,
                        max(0.5, y_cursor - 0.8),
                        f"长度: {int(useful_length)}",
                        ha="center",
                        va="top",
                        fontsize=8,
                        color="black",
                    )

                if stage_width >= narrow_stage_threshold and item_width * scale_y > 8:
                    ax.text(
                        max(0.5, current_x - 0.8),
                        y_cursor + item_width * scale_y / 2,
                        f"宽度: {int(item_width)}",
                        ha="right",
                        va="center",
                        fontsize=8,
                        color="black",
                        rotation="vertical",
                    )

                y_cursor += item_width * scale_y

            if waste_length > 0:
                candidate_tail = {
                    "waste_length": waste_length,
                    "xy": (
                        current_x + useful_length_scaled + waste_length_scaled / 2,
                        group_start_y + lane_count * item_width * scale_y / 2,
                    ),
                    "xytext": (
                        current_x + stage_width + 1.4,
                        min(
                            PANEL_WIDTH * scale_y + 5.8,
                            group_start_y + lane_count * item_width * scale_y + 2.0,
                        ),
                    ),
                }
                if largest_tail is None or candidate_tail["waste_length"] > largest_tail["waste_length"]:
                    largest_tail = candidate_tail

        if largest_tail is not None:
            tail_annotations.append(largest_tail)

        label_y = PANEL_WIDTH * scale_y + 1.6
        max_label_y = max(max_label_y, label_y)
        should_draw_stage_label = len(strips) <= 12 or stage_width >= narrow_stage_threshold
        if should_draw_stage_label:
            ax.text(
                current_x + stage_width / 2,
                label_y,
                f"模式{stage_index}",
                ha="center",
                va="bottom",
                fontsize=8,
                color="black",
            )

        if stage_width < narrow_stage_threshold:
            zoom_cards.append(
                {
                    "stage_index": stage_index,
                    "stage_groups": [
                        {
                            **group,
                            "display_quantity": actual_repeat_count * group["lane_count"],
                        }
                        for group in stage_groups
                    ],
                    "used_width": used_width,
                    "stage_width": stage_width,
                    "lane_total": sum(group["lane_count"] for group in stage_groups),
                    "anchor": (
                        current_x + stage_width / 2,
                        PANEL_WIDTH * scale_y * 0.78,
                    ),
                    "title": f"模式{stage_index} 放大",
                }
            )

        current_x += stage_width

    if len(summary_lines) > max_summary_lines:
        hidden_count = len(summary_lines) - max_summary_lines
        summary_display_lines = summary_lines[:max_summary_lines] + [f"... 其余 {hidden_count} 个模式已省略"]
    else:
        summary_display_lines = summary_lines

    summary_y = max_label_y + 3.0
    ax.text(
        0.0,
        summary_y,
        "\n".join(summary_display_lines),
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

    for annotation in tail_annotations:
        ax.annotate(
            f"余料 {int(annotation['waste_length'])}",
            xy=annotation["xy"],
            xytext=annotation["xytext"],
            fontsize=7,
            color="#555",
            ha="left",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "#c9cfd6",
                "alpha": 0.95,
            },
            arrowprops={
                "arrowstyle": "->",
                "color": "#7f8c8d",
                "linewidth": 0.9,
                "shrinkA": 3,
                "shrinkB": 2,
            },
        )

    zoom_cards = sorted(
        zoom_cards,
        key=lambda item: (item["stage_width"], item["lane_total"], item["stage_index"]),
    )[:max_zoom_cards]

    right_margin = 4.0
    if zoom_cards:
        card_width = 22.0
        card_height = 27.0
        card_gap = 3.0
        card_x = total_length * scale_x + 6.0
        card_y = PANEL_WIDTH * scale_y - card_height
        for card in zoom_cards:
            _draw_stage_zoom_card(
                ax,
                card,
                card_x,
                card_y,
                card_width,
                card_height,
                color_map,
            )
            card_y -= card_height + card_gap
        right_margin = card_width + 10.0

    legend_handles = [
        patches.Patch(
            facecolor=color_map[type_id],
            edgecolor="white",
            label=f"T{type_id + 1}",
        )
        for type_id in type_ids
    ]
    legend_handles.append(
        patches.Patch(
            facecolor="#d9dde3",
            edgecolor="#7f8c8d",
            hatch="///",
            label="条带尾部余料",
        )
    )
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        bbox_to_anchor=(1.0, 0.98),
        fontsize=8,
        frameon=True,
    )

    ax.set_xlim(-2, total_length * scale_x + right_margin)
    ax.set_ylim(-2, summary_y + 10)
    ax.axis("off")
    ax.set_title(f"面积利用率: {efficiency:.2f}%", fontsize=14)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"压缩排版图已保存至: {save_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_compact_cutting_plan(strips, repeat_counts, efficiency, save_path=None, show=True):
    """
    汇报版 simple / best_fit 压缩排布图：
    1. 优先展示长度贡献最大的少量模式；
    2. 次要模式收纳到摘要文字里，不强行全部画出；
    3. 过窄模式最多保留 3 个放大卡片；
    4. 主图与放大图均显示实际数量，而非缩放后的编码数量。
    """
    entries = []
    for stage_index, (strip, repeat_count) in enumerate(zip(strips, repeat_counts), start=1):
        actual_repeat_count = repeat_count * SCALE_FACTOR
        stage_groups = _collect_stage_groups(strip)
        combo_text, width_text, used_width = _format_stage_combination(stage_groups)
        entries.append(
            {
                "stage_index": stage_index,
                "strip": strip,
                "repeat_count": repeat_count,
                "actual_repeat_count": actual_repeat_count,
                "stage_groups": stage_groups,
                "combo_text": combo_text,
                "width_text": width_text,
                "used_width": used_width,
                "stage_length": strip.strip_length * actual_repeat_count,
            }
        )

    if not entries:
        return

    display_limit = 6 if len(entries) > 8 else len(entries)
    top_stage_ids = {
        entry["stage_index"]
        for entry in sorted(entries, key=lambda item: item["stage_length"], reverse=True)[:display_limit]
    }
    display_entries = [entry for entry in entries if entry["stage_index"] in top_stage_ids]
    omitted_entries = [entry for entry in entries if entry["stage_index"] not in top_stage_ids]

    total_length = sum(entry["stage_length"] for entry in display_entries)
    if total_length <= 0:
        return

    figure_x = 205.0
    figure_y = 100.0
    scale_x = figure_x / total_length
    scale_y = figure_y / PANEL_WIDTH

    fig, ax = plt.subplots(figsize=(14, 8))

    type_ids = sorted({item.type_id for entry in display_entries for item in entry["strip"].items})
    palette = plt.cm.tab20(np.linspace(0.08, 0.92, max(1, len(type_ids))))
    color_map = {type_id: palette[i % len(palette)] for i, type_id in enumerate(type_ids)}

    bg = patches.Rectangle(
        (0, 0),
        total_length * scale_x,
        PANEL_WIDTH * scale_y,
        facecolor="#eef1f4",
        edgecolor="black",
        linewidth=1.4,
        alpha=0.95,
    )
    ax.add_patch(bg)

    current_x = 0.0
    max_label_y = PANEL_WIDTH * scale_y
    summary_lines = []
    tail_annotations = []
    zoom_cards = []
    narrow_stage_threshold = 16.0
    max_tail_annotations = 3
    max_zoom_cards = 3

    for entry in display_entries:
        stage_index = entry["stage_index"]
        stage_length = entry["stage_length"]
        stage_width = stage_length * scale_x
        stage_groups = entry["stage_groups"]

        summary_lines.append(
            f"模式{stage_index}: {entry['combo_text']}   宽度组合: {entry['width_text']} = {int(entry['used_width'])}   重复: {int(entry['actual_repeat_count'])}"
        )

        stage_outline = patches.Rectangle(
            (current_x, 0),
            stage_width,
            PANEL_WIDTH * scale_y,
            facecolor="none",
            edgecolor="#9aa4b2",
            linewidth=1.0,
            alpha=0.8,
        )
        ax.add_patch(stage_outline)

        y_cursor = 0.0
        largest_tail = None
        for group in stage_groups:
            type_id = group["type_id"]
            item_width = group["width"]
            item_length = group["length"]
            lane_count = group["lane_count"]
            useful_length = item_length * entry["actual_repeat_count"]
            useful_length_scaled = useful_length * scale_x
            waste_length = max(0, stage_length - useful_length)
            waste_length_scaled = waste_length * scale_x
            color = color_map[type_id]
            group_start_y = y_cursor
            quantity = entry["actual_repeat_count"] * lane_count

            for _ in range(lane_count):
                rect = patches.Rectangle(
                    (current_x, y_cursor),
                    useful_length_scaled,
                    item_width * scale_y,
                    facecolor=color,
                    edgecolor="red",
                    linewidth=1.1,
                )
                ax.add_patch(rect)

                if waste_length_scaled > 0:
                    waste_rect = patches.Rectangle(
                        (current_x + useful_length_scaled, y_cursor),
                        waste_length_scaled,
                        item_width * scale_y,
                        facecolor="#d9dde3",
                        edgecolor="#7f8c8d",
                        linewidth=0.8,
                        hatch="///",
                        alpha=0.95,
                    )
                    ax.add_patch(waste_rect)

                if stage_width >= narrow_stage_threshold and useful_length_scaled > 10 and item_width * scale_y > 10:
                    ax.text(
                        current_x + useful_length_scaled / 2,
                        y_cursor + item_width * scale_y / 2,
                        f"T{type_id + 1}\n数量:{quantity}",
                        ha="center",
                        va="center",
                        fontsize=8,
                        color="white",
                        fontweight="bold",
                    )
                y_cursor += item_width * scale_y

            if stage_width >= narrow_stage_threshold and useful_length_scaled > 18:
                ax.text(
                    current_x + useful_length_scaled / 2,
                    max(0.6, group_start_y - 0.7),
                    f"长度: {int(useful_length)}",
                    ha="center",
                    va="top",
                    fontsize=7,
                    color="#333",
                )

            if waste_length > 0:
                candidate_tail = {
                    "waste_length": waste_length,
                    "xy": (
                        current_x + useful_length_scaled + waste_length_scaled / 2,
                        group_start_y + lane_count * item_width * scale_y / 2,
                    ),
                    "xytext": (
                        current_x + stage_width + 1.5,
                        min(PANEL_WIDTH * scale_y + 4.8, group_start_y + lane_count * item_width * scale_y + 1.5),
                    ),
                }
                if largest_tail is None or candidate_tail["waste_length"] > largest_tail["waste_length"]:
                    largest_tail = candidate_tail

        if largest_tail is not None:
            tail_annotations.append(largest_tail)

        label_y = PANEL_WIDTH * scale_y + 1.5
        max_label_y = max(max_label_y, label_y)
        if stage_width >= narrow_stage_threshold:
            ax.text(
                current_x + stage_width / 2,
                label_y,
                f"模式{stage_index}",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#333",
            )

        if stage_width < narrow_stage_threshold:
            zoom_cards.append(
                {
                    "stage_index": stage_index,
                    "stage_groups": [
                        {
                            **group,
                            "display_quantity": entry["actual_repeat_count"] * group["lane_count"],
                        }
                        for group in stage_groups
                    ],
                    "used_width": entry["used_width"],
                    "stage_width": stage_width,
                    "lane_total": sum(group["lane_count"] for group in stage_groups),
                    "anchor": (
                        current_x + stage_width / 2,
                        PANEL_WIDTH * scale_y * 0.72,
                    ),
                    "title": f"模式{stage_index} 放大",
                }
            )

        current_x += stage_width

    summary_display_lines = summary_lines[:4]
    if omitted_entries:
        omitted_length = sum(entry["stage_length"] for entry in omitted_entries)
        summary_display_lines.append(
            f"... 其余 {len(omitted_entries)} 个次要模式已省略，合计长度 {int(omitted_length)}"
        )

    summary_y = max_label_y + 2.8
    ax.text(
        0.0,
        summary_y,
        "\n".join(summary_display_lines),
        ha="left",
        va="bottom",
        fontsize=8,
        color="#222",
        bbox={
            "facecolor": "white",
            "edgecolor": "#d4d8dd",
            "alpha": 0.96,
            "boxstyle": "round,pad=0.35",
        },
    )

    tail_annotations = sorted(
        tail_annotations,
        key=lambda item: item["waste_length"],
        reverse=True,
    )[:max_tail_annotations]
    for annotation in tail_annotations:
        ax.annotate(
            f"余料 {int(annotation['waste_length'])}",
            xy=annotation["xy"],
            xytext=annotation["xytext"],
            fontsize=7,
            color="#555",
            ha="left",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "#c9cfd6",
                "alpha": 0.95,
            },
            arrowprops={
                "arrowstyle": "->",
                "color": "#7f8c8d",
                "linewidth": 0.9,
                "shrinkA": 3,
                "shrinkB": 2,
            },
        )

    zoom_cards = sorted(
        zoom_cards,
        key=lambda item: (item["stage_width"], item["lane_total"], item["stage_index"]),
    )[:max_zoom_cards]

    right_margin = 4.0
    if zoom_cards:
        card_width = 20.0
        card_height = 24.0
        card_gap = 2.8
        card_x = total_length * scale_x + 5.0
        card_y = PANEL_WIDTH * scale_y - card_height
        for card in zoom_cards:
            _draw_stage_zoom_card(
                ax,
                card,
                card_x,
                card_y,
                card_width,
                card_height,
                color_map,
            )
            card_y -= card_height + card_gap
        right_margin = card_width + 8.0

    legend_handles = [
        patches.Patch(
            facecolor=color_map[type_id],
            edgecolor="white",
            label=f"T{type_id + 1}",
        )
        for type_id in type_ids
    ]
    legend_handles.append(
        patches.Patch(
            facecolor="#d9dde3",
            edgecolor="#7f8c8d",
            hatch="///",
            label="条带尾部余料",
        )
    )
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        bbox_to_anchor=(1.0, 0.98),
        fontsize=8,
        frameon=True,
    )

    ax.set_xlim(-1, total_length * scale_x + right_margin)
    ax.set_ylim(-1, summary_y + 9)
    ax.axis("off")
    ax.set_title(f"面积利用率: {efficiency:.2f}%", fontsize=14)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"压缩排版图已保存至: {save_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_compact_cutting_plan(strips, repeat_counts, efficiency, save_path=None, show=True):
    """
    Presentation-friendly compact plot for simple / best_fit decoders.
    The main panel focuses on dominant modes and uses compressed horizontal
    widths for readability. Narrow or dense modes are explained with up to
    three zoom cards on the right.
    """
    entries = []
    for stage_index, (strip, repeat_count) in enumerate(zip(strips, repeat_counts), start=1):
        actual_repeat_count = repeat_count * SCALE_FACTOR
        stage_groups = _collect_stage_groups(strip)
        combo_text, width_text, used_width = _format_stage_combination(stage_groups)
        entries.append(
            {
                "stage_index": stage_index,
                "strip": strip,
                "repeat_count": repeat_count,
                "actual_repeat_count": actual_repeat_count,
                "stage_groups": stage_groups,
                "combo_text": combo_text,
                "width_text": width_text,
                "used_width": used_width,
                "stage_length": strip.strip_length * actual_repeat_count,
            }
        )

    if not entries:
        return

    max_display_stages = 5 if len(entries) > 5 else len(entries)
    ranked_entries = sorted(entries, key=lambda item: item["stage_length"], reverse=True)
    display_entries = ranked_entries[:max_display_stages]
    omitted_entries = ranked_entries[max_display_stages:]

    display_total_length = sum(entry["stage_length"] for entry in display_entries)
    if display_total_length <= 0:
        return

    panel_width = 152.0
    panel_height = 100.0
    scale_y = panel_height / PANEL_WIDTH

    fig, ax = plt.subplots(figsize=(15.5, 8.6))

    type_ids = sorted({item.type_id for entry in display_entries for item in entry["strip"].items})
    palette = plt.cm.tab20(np.linspace(0.08, 0.92, max(1, len(type_ids))))
    color_map = {type_id: palette[i % len(palette)] for i, type_id in enumerate(type_ids)}

    bg = patches.Rectangle(
        (0, 0),
        panel_width,
        panel_height,
        facecolor="#eef1f4",
        edgecolor="black",
        linewidth=1.4,
        alpha=0.95,
    )
    ax.add_patch(bg)

    visual_weights = [max(1.0, float(np.sqrt(entry["stage_length"]))) for entry in display_entries]
    visual_weight_sum = sum(visual_weights) if visual_weights else 1.0
    stage_widths = [panel_width * weight / visual_weight_sum for weight in visual_weights]

    current_x = 0.0
    summary_lines = []
    tail_annotations = []
    zoom_candidates = []
    narrow_stage_threshold = 24.0
    max_tail_annotations = 2
    max_zoom_cards = 3

    for entry, stage_width in zip(display_entries, stage_widths):
        stage_index = entry["stage_index"]
        stage_length = entry["stage_length"]
        stage_groups = entry["stage_groups"]
        lane_total = sum(group["lane_count"] for group in stage_groups)
        stage_x = current_x

        summary_lines.append(
            f"模式{stage_index}: {entry['combo_text']} | 重复 {int(entry['actual_repeat_count'])} | 总长 {int(stage_length)}"
        )

        stage_outline = patches.Rectangle(
            (stage_x, 0),
            stage_width,
            panel_height,
            facecolor="#f8fafc",
            edgecolor="#96a0ad",
            linewidth=1.0,
            alpha=1.0,
        )
        ax.add_patch(stage_outline)

        y_cursor = 0.0
        largest_tail = None
        for group in stage_groups:
            type_id = group["type_id"]
            item_width = group["width"]
            item_length = group["length"]
            lane_count = group["lane_count"]
            useful_length = item_length * entry["actual_repeat_count"]
            waste_length = max(0, stage_length - useful_length)
            useful_ratio = useful_length / stage_length if stage_length > 0 else 0.0
            useful_length_scaled = stage_width * useful_ratio
            waste_length_scaled = max(0.0, stage_width - useful_length_scaled)
            color = color_map[type_id]
            group_start_y = y_cursor
            lane_quantity = entry["actual_repeat_count"]

            for _ in range(lane_count):
                lane_height = item_width * scale_y
                rect = patches.Rectangle(
                    (stage_x, y_cursor),
                    useful_length_scaled,
                    lane_height,
                    facecolor=color,
                    edgecolor="red",
                    linewidth=1.1,
                )
                ax.add_patch(rect)

                if waste_length_scaled > 0:
                    waste_rect = patches.Rectangle(
                        (stage_x + useful_length_scaled, y_cursor),
                        waste_length_scaled,
                        lane_height,
                        facecolor="#d9dde3",
                        edgecolor="#7f8c8d",
                        linewidth=0.8,
                        hatch="///",
                        alpha=0.95,
                    )
                    ax.add_patch(waste_rect)

                if stage_width >= narrow_stage_threshold and useful_length_scaled > 7 and lane_height > 8:
                    ax.text(
                        stage_x + useful_length_scaled / 2,
                        y_cursor + lane_height / 2,
                        f"T{type_id + 1}\n数量:{int(lane_quantity)}",
                        ha="center",
                        va="center",
                        fontsize=7.6,
                        color="white",
                        fontweight="bold",
                    )

                y_cursor += lane_height

            if stage_width >= 30 and useful_length_scaled > 13:
                ax.text(
                    stage_x + useful_length_scaled / 2,
                    max(0.8, group_start_y - 0.8),
                    f"长度: {int(useful_length)}",
                    ha="center",
                    va="top",
                    fontsize=7,
                    color="#333",
                )

            if waste_length > 0:
                candidate_tail = {
                    "waste_length": waste_length,
                    "xy": (
                        stage_x + useful_length_scaled + waste_length_scaled / 2,
                        group_start_y + lane_count * item_width * scale_y / 2,
                    ),
                    "xytext": (
                        stage_x + stage_width + 1.4,
                        min(panel_height - 4.0, group_start_y + lane_count * item_width * scale_y + 2.0),
                    ),
                }
                if largest_tail is None or candidate_tail["waste_length"] > largest_tail["waste_length"]:
                    largest_tail = candidate_tail

        if largest_tail is not None:
            tail_annotations.append(largest_tail)

        ax.text(
            stage_x + stage_width / 2,
            panel_height + 1.8,
            f"模式{stage_index}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#333",
            fontweight="bold",
        )
        ax.text(
            stage_x + stage_width / 2,
            panel_height + 5.1,
            f"总长 {int(stage_length)}",
            ha="center",
            va="bottom",
            fontsize=7,
            color="#56606c",
        )

        if stage_width < narrow_stage_threshold or lane_total >= 4:
            zoom_candidates.append(
                {
                    "stage_index": stage_index,
                    "stage_groups": [
                        {
                            **group,
                            "display_quantity": entry["actual_repeat_count"] * group["lane_count"],
                        }
                        for group in stage_groups
                    ],
                    "used_width": entry["used_width"],
                    "stage_width": stage_width,
                    "lane_total": lane_total,
                    "anchor": (
                        stage_x + stage_width * 0.92,
                        panel_height * 0.72,
                    ),
                    "title": f"模式{stage_index} 放大",
                }
            )

        current_x += stage_width

    summary_display_lines = [
        f"主图展示长度贡献最大的 {len(display_entries)} 个模式，横向按相对贡献压缩示意，块内长度/数量为实际值。"
    ]
    summary_display_lines.extend(summary_lines[:max_display_stages])
    if omitted_entries:
        omitted_length = sum(entry["stage_length"] for entry in omitted_entries)
        summary_display_lines.append(
            f"其余 {len(omitted_entries)} 个次要模式已省略，累计总长 {int(omitted_length)}。"
        )
    summary_display_lines.append("窄模式或条带过密模式在右侧放大，放大图最多保留 3 个。")

    summary_y = panel_height + 10.0
    ax.text(
        0.0,
        summary_y,
        "\n".join(summary_display_lines),
        ha="left",
        va="bottom",
        fontsize=8,
        color="#222",
        bbox={
            "facecolor": "white",
            "edgecolor": "#d4d8dd",
            "alpha": 0.96,
            "boxstyle": "round,pad=0.35",
        },
    )

    tail_annotations = sorted(tail_annotations, key=lambda item: item["waste_length"], reverse=True)[:max_tail_annotations]
    for annotation in tail_annotations:
        ax.annotate(
            f"余料 {int(annotation['waste_length'])}",
            xy=annotation["xy"],
            xytext=annotation["xytext"],
            fontsize=7,
            color="#555",
            ha="left",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "#c9cfd6",
                "alpha": 0.95,
            },
            arrowprops={
                "arrowstyle": "->",
                "color": "#7f8c8d",
                "linewidth": 0.9,
                "shrinkA": 3,
                "shrinkB": 2,
            },
        )

    zoom_cards = sorted(
        zoom_candidates,
        key=lambda item: (item["stage_width"], -item["lane_total"], item["stage_index"]),
    )[:max_zoom_cards]

    right_margin = 4.0
    if zoom_cards:
        card_width = 24.0
        card_height = 22.5
        card_gap = 3.0
        card_x = panel_width + 4.0
        card_y = panel_height - card_height
        for card in zoom_cards:
            _draw_stage_zoom_card(
                ax,
                card,
                card_x,
                card_y,
                card_width,
                card_height,
                color_map,
            )
            card_y -= card_height + card_gap
        right_margin = card_width + 8.5

    legend_handles = [
        patches.Patch(
            facecolor=color_map[type_id],
            edgecolor="white",
            label=f"T{type_id + 1}",
        )
        for type_id in type_ids
    ]
    legend_handles.append(
        patches.Patch(
            facecolor="#d9dde3",
            edgecolor="#7f8c8d",
            hatch="///",
            label="条带尾部余料",
        )
    )
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        bbox_to_anchor=(1.0, 0.92),
        fontsize=8,
        frameon=True,
    )

    ax.set_xlim(-1.5, panel_width + right_margin)
    ax.set_ylim(-1.5, summary_y + 12.0)
    ax.axis("off")
    ax.set_title(f"面积利用率: {efficiency:.2f}%", fontsize=14, pad=16)

    plt.subplots_adjust(left=0.03, right=0.98, top=0.90, bottom=0.04)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"紧凑排布图已保存至: {save_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_compact_cutting_plan(strips, repeat_counts, efficiency, save_path=None, show=True):
    """
    Full compact plot for simple / best_fit decoders.
    Show all merged strips, suppress labels on very narrow strips, and do not
    create zoom cards for tiny stages. Waste information is preserved for
    every strip at the top of the plot.
    """
    entries = []
    for stage_index, (strip, repeat_count) in enumerate(zip(strips, repeat_counts), start=1):
        actual_repeat_count = repeat_count * SCALE_FACTOR
        stage_groups = _collect_stage_groups(strip)
        combo_text, width_text, used_width = _format_stage_combination(stage_groups)
        entries.append(
            {
                "stage_index": stage_index,
                "strip": strip,
                "repeat_count": repeat_count,
                "actual_repeat_count": actual_repeat_count,
                "stage_groups": stage_groups,
                "combo_text": combo_text,
                "width_text": width_text,
                "used_width": used_width,
                "stage_length": strip.strip_length * actual_repeat_count,
            }
        )

    if not entries:
        return

    panel_width = 220.0 if len(entries) > 12 else 180.0
    panel_height = 100.0
    stage_gap = 0.6
    scale_y = panel_height / PANEL_WIDTH
    fig, ax = plt.subplots(figsize=(18.5, 9.4))

    type_ids = sorted({item.type_id for entry in entries for item in entry["strip"].items})
    palette = plt.cm.tab20(np.linspace(0.08, 0.92, max(1, len(type_ids))))
    color_map = {type_id: palette[i % len(palette)] for i, type_id in enumerate(type_ids)}

    bg = patches.Rectangle(
        (0, 0),
        panel_width,
        panel_height,
        facecolor="#eef1f4",
        edgecolor="black",
        linewidth=1.4,
        alpha=0.95,
    )
    ax.add_patch(bg)

    stage_count = len(entries)
    total_gap = stage_gap * max(0, stage_count - 1)
    available_width = panel_width - total_gap
    min_stage_width = 5.4 if stage_count > 12 else 7.0
    min_stage_total = min_stage_width * stage_count
    base_width = min(min_stage_total, available_width * 0.7)
    residual_width = max(0.0, available_width - base_width)
    visual_weights = [max(1.0, float(np.sqrt(entry["stage_length"]))) for entry in entries]
    visual_weight_sum = sum(visual_weights) if visual_weights else 1.0
    stage_widths = [
        base_width / stage_count + residual_width * weight / visual_weight_sum
        for weight in visual_weights
    ]

    current_x = 0.0
    internal_label_threshold = 11.5
    stage_label_threshold = 8.5
    waste_label_threshold = 7.0

    for idx, (entry, stage_width) in enumerate(zip(entries, stage_widths)):
        stage_index = entry["stage_index"]
        stage_length = entry["stage_length"]
        stage_groups = entry["stage_groups"]
        stage_x = current_x

        stage_outline = patches.Rectangle(
            (stage_x, 0),
            stage_width,
            panel_height,
            facecolor="#f8fafc",
            edgecolor="#96a0ad",
            linewidth=0.95,
            alpha=1.0,
        )
        ax.add_patch(stage_outline)

        y_cursor = 0.0
        waste_values = []
        for group in stage_groups:
            type_id = group["type_id"]
            item_width = group["width"]
            item_length = group["length"]
            lane_count = group["lane_count"]
            useful_length = item_length * entry["actual_repeat_count"]
            waste_length = max(0, stage_length - useful_length)
            useful_ratio = useful_length / stage_length if stage_length > 0 else 0.0
            useful_length_scaled = stage_width * useful_ratio
            waste_length_scaled = max(0.0, stage_width - useful_length_scaled)
            color = color_map[type_id]
            lane_quantity = entry["actual_repeat_count"]

            if waste_length > 0:
                waste_values.append(int(waste_length))

            for _ in range(lane_count):
                lane_height = item_width * scale_y
                rect = patches.Rectangle(
                    (stage_x, y_cursor),
                    useful_length_scaled,
                    lane_height,
                    facecolor=color,
                    edgecolor="red",
                    linewidth=1.0,
                )
                ax.add_patch(rect)

                if waste_length_scaled > 0:
                    waste_rect = patches.Rectangle(
                        (stage_x + useful_length_scaled, y_cursor),
                        waste_length_scaled,
                        lane_height,
                        facecolor="#d9dde3",
                        edgecolor="#7f8c8d",
                        linewidth=0.75,
                        hatch="///",
                        alpha=0.95,
                    )
                    ax.add_patch(waste_rect)

                if stage_width >= internal_label_threshold and useful_length_scaled > 6.5 and lane_height > 8:
                    ax.text(
                        stage_x + useful_length_scaled / 2,
                        y_cursor + lane_height / 2,
                        f"T{type_id + 1}\n数量:{int(lane_quantity)}",
                        ha="center",
                        va="center",
                        fontsize=6.9,
                        color="white",
                        fontweight="bold",
                    )

                y_cursor += lane_height

        waste_text = "/".join(str(v) for v in sorted(set(waste_values))) if waste_values else "0"

        if stage_width >= stage_label_threshold:
            ax.text(
                stage_x + stage_width / 2,
                panel_height + 1.8,
                f"模式{stage_index}",
                ha="center",
                va="bottom",
                fontsize=7.1,
                color="#333",
                fontweight="bold",
            )

        if stage_width >= waste_label_threshold:
            ax.text(
                stage_x + stage_width / 2,
                panel_height + 5.0 + (idx % 3) * 1.8,
                f"余料 {waste_text}",
                ha="center",
                va="bottom",
                fontsize=6.4,
                color="#56606c",
                bbox={
                    "facecolor": "white",
                    "edgecolor": "#d4d8dd",
                    "alpha": 0.88,
                    "boxstyle": "round,pad=0.18",
                },
            )
        else:
            ax.text(
                stage_x + stage_width / 2,
                panel_height + 3.5 + (idx % 3) * 2.0,
                f"余{waste_text}",
                ha="center",
                va="bottom",
                fontsize=5.8,
                color="#56606c",
                rotation=90,
            )

        current_x += stage_width + stage_gap

    summary_y = panel_height + 13.0
    summary_text = (
        f"完整图：已展示全部 {len(entries)} 个模式，横向长度为压缩示意；"
        "过窄 strip 不显示内部标签，也不再使用放大图；每个 strip 顶部保留余料信息。"
    )
    ax.text(
        0.0,
        summary_y,
        summary_text,
        ha="left",
        va="bottom",
        fontsize=8,
        color="#222",
        bbox={
            "facecolor": "white",
            "edgecolor": "#d4d8dd",
            "alpha": 0.96,
            "boxstyle": "round,pad=0.35",
        },
    )

    legend_handles = [
        patches.Patch(
            facecolor=color_map[type_id],
            edgecolor="white",
            label=f"T{type_id + 1}",
        )
        for type_id in type_ids
    ]
    legend_handles.append(
        patches.Patch(
            facecolor="#d9dde3",
            edgecolor="#7f8c8d",
            hatch="///",
            label="条带尾部余料",
        )
    )
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        bbox_to_anchor=(1.0, 0.96),
        fontsize=8,
        frameon=True,
    )

    ax.set_xlim(-1.0, panel_width + 1.0)
    ax.set_ylim(-1.5, summary_y + 10.0)
    ax.axis("off")
    ax.set_title(f"面积利用率: {efficiency:.2f}%", fontsize=14, pad=16)

    plt.subplots_adjust(left=0.03, right=0.985, top=0.90, bottom=0.04)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"完整排布图已保存至: {save_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_compact_cutting_plan(strips, repeat_counts, efficiency, save_path=None, show=True):
    """
    Draw simple / best_fit results with the same visual structure as the
    stage_based layout. Narrow stages are not labeled and are not zoomed.
    """
    total_length = sum(strip.strip_length * count * SCALE_FACTOR for strip, count in zip(strips, repeat_counts))
    if total_length <= 0:
        return

    figure_x = 205.0
    figure_y = 100.0
    scale_x = figure_x / total_length
    scale_y = figure_y / PANEL_WIDTH

    fig, ax = plt.subplots(figsize=(16, 9))

    type_ids = sorted({item.type_id for strip in strips for item in strip.items})
    palette = plt.cm.tab20(np.linspace(0.08, 0.92, max(1, len(type_ids))))
    color_map = {type_id: palette[i % len(palette)] for i, type_id in enumerate(type_ids)}

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
    tail_annotations = []
    narrow_stage_threshold = 12.0

    for stage_index, (strip, repeat_count) in enumerate(zip(strips, repeat_counts), start=1):
        actual_repeat_count = repeat_count * SCALE_FACTOR
        stage_length = strip.strip_length * actual_repeat_count
        stage_length_scaled = stage_length * scale_x
        stage_groups = _collect_stage_groups(strip)
        combo_text, width_text, used_width = _format_stage_combination(stage_groups)
        summary_lines.append(
            f"模式{stage_index}: {combo_text}   宽度组合: {width_text} = {int(used_width)}   重复: {int(actual_repeat_count)}"
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
        largest_tail = None

        for group in stage_groups:
            item_width = group["width"]
            item_length = group["length"]
            lane_count = group["lane_count"]
            lane_quantity = actual_repeat_count
            lane_length = item_length * lane_quantity
            lane_length_scaled = lane_length * scale_x
            waste_length = max(0, stage_length - lane_length)
            waste_length_scaled = waste_length * scale_x
            color = color_map[group["type_id"]]
            group_start_y = y_cursor
            lane_height = item_width * scale_y

            for _ in range(lane_count):
                rect = patches.Rectangle(
                    (current_x, y_cursor),
                    lane_length_scaled,
                    lane_height,
                    facecolor=color,
                    edgecolor="red",
                    linewidth=1.2,
                )
                ax.add_patch(rect)

                if waste_length_scaled > 0:
                    waste_rect = patches.Rectangle(
                        (current_x + lane_length_scaled, y_cursor),
                        waste_length_scaled,
                        lane_height,
                        facecolor="#d9dde3",
                        edgecolor="#7f8c8d",
                        linewidth=0.9,
                        hatch="///",
                        alpha=0.95,
                    )
                    ax.add_patch(waste_rect)

                if stage_length_scaled >= narrow_stage_threshold and lane_length_scaled > 8 and lane_height > 8:
                    ax.text(
                        current_x + lane_length_scaled / 2,
                        y_cursor + lane_height / 2,
                        f"T{group['type_id'] + 1}\n数量:{int(lane_quantity)}",
                        ha="center",
                        va="center",
                        color="white",
                        fontsize=9,
                        fontweight="bold",
                    )

                if stage_length_scaled >= narrow_stage_threshold and lane_length_scaled > 10:
                    ax.text(
                        current_x + lane_length_scaled / 2,
                        max(0.6, y_cursor - 0.8),
                        f"长度: {int(lane_length)}",
                        ha="center",
                        va="top",
                        color="black",
                        fontsize=8,
                    )

                if stage_length_scaled >= narrow_stage_threshold and lane_height > 7:
                    ax.text(
                        max(0.4, current_x - 0.8),
                        y_cursor + lane_height / 2,
                        f"宽度: {int(item_width)}",
                        ha="right",
                        va="center",
                        color="black",
                        fontsize=8,
                        rotation="vertical",
                    )

                y_cursor += lane_height

            if waste_length > 0 and stage_length_scaled >= narrow_stage_threshold:
                candidate_tail = {
                    "waste_length": waste_length,
                    "xy": (
                        current_x + lane_length_scaled + waste_length_scaled / 2,
                        group_start_y + lane_count * lane_height / 2,
                    ),
                    "xytext": (
                        current_x + stage_length_scaled + 1.4,
                        min(
                            PANEL_WIDTH * scale_y + 5.8,
                            group_start_y + lane_count * lane_height + 2.0,
                        ),
                    ),
                }
                if largest_tail is None or candidate_tail["waste_length"] > largest_tail["waste_length"]:
                    largest_tail = candidate_tail

        if largest_tail is not None:
            tail_annotations.append(largest_tail)

        stage_label_y = PANEL_WIDTH * scale_y + 1.6
        max_stage_label_y = max(max_stage_label_y, stage_label_y)
        if stage_length_scaled >= narrow_stage_threshold:
            ax.text(
                current_x + stage_length_scaled / 2,
                stage_label_y,
                f"模式{stage_index}",
                ha="center",
                va="bottom",
                fontsize=8,
                color="black",
            )

        current_x += stage_length_scaled

    max_summary_lines = 8 if len(summary_lines) > 8 else len(summary_lines)
    summary_display_lines = summary_lines[:max_summary_lines]
    if len(summary_lines) > max_summary_lines:
        summary_display_lines.append(f"... 其余 {len(summary_lines) - max_summary_lines} 个模式省略")

    summary_y = max_stage_label_y + 3.0
    ax.text(
        0.0,
        summary_y,
        "\n".join(summary_display_lines),
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

    for annotation in tail_annotations:
        ax.annotate(
            f"余料 {int(annotation['waste_length'])}",
            xy=annotation["xy"],
            xytext=annotation["xytext"],
            fontsize=7,
            color="#555",
            ha="left",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "#c9cfd6",
                "alpha": 0.95,
            },
            arrowprops={
                "arrowstyle": "->",
                "color": "#7f8c8d",
                "linewidth": 0.9,
                "shrinkA": 3,
                "shrinkB": 2,
            },
        )

    legend_handles = [
        patches.Patch(
            facecolor=color_map[type_id],
            edgecolor="white",
            label=f"T{type_id + 1}",
        )
        for type_id in type_ids
    ]
    legend_handles.append(
        patches.Patch(
            facecolor="#d9dde3",
            edgecolor="#7f8c8d",
            hatch="///",
            label="条带尾部余料",
        )
    )
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        bbox_to_anchor=(1.0, 0.98),
        fontsize=8,
        frameon=True,
    )

    ax.set_xlim(-2, total_length * scale_x + 4.0)
    ax.set_ylim(-2, summary_y + 10)
    ax.axis("off")
    ax.set_title(f"面积利用率: {efficiency:.2f}%", fontsize=14)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"阶段风格排布图已保存至: {save_path}")

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
