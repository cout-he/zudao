# -*- coding: utf-8 -*-
"""
可视化模块 - 切割方案可视化和进化过程可视化
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from config import PANEL_WIDTH

# 图片显示中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def plot_cutting_plan(strips, items, type_info, efficiency, save_path=None):
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
    
    plt.show()


def plot_evolution_history(history, save_path=None):
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
    
    plt.show()


def plot_strip_details(strips, type_info, save_path=None):
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
    
    plt.show()


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
    from data_loader import load_demand_from_excel, expand_demand
    from decoder import decode
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
