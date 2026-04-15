from collections import defaultdict
from pathlib import Path

from core.config import PANEL_WIDTH, SCALE_FACTOR
from core.decoder import merge_same_pattern_strips


def _collect_lane_groups(strip):
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


def _format_width_combo(groups):
    return " + ".join([str(int(group["width"])) for group in groups for _ in range(group["lane_count"])])


def _format_knife_positions(groups):
    positions = []
    cursor = 0
    for group in groups:
        for _ in range(group["lane_count"]):
            cursor += int(group["width"])
            positions.append(cursor)
    return " / ".join(str(pos) for pos in positions)


def _format_demand_section(demand):
    lines = ["一、订单信息", ""]
    for idx, (width, length, num) in enumerate(zip(demand["Width"], demand["Length"], demand["num"]), start=1):
        lines.append(f"T{idx}: 宽 {int(width)} mm，长 {int(length)} mm，订单数量 {int(num)} 件")
    return lines


def _format_summary_section(sheet_num, decoder_mode, demand, solution):
    total_area_demand = sum(
        width * length * num
        for width, length, num in zip(demand["Width"], demand["Length"], demand["num"])
    )
    real_total_length = solution["total_length"] * SCALE_FACTOR
    total_area_used = PANEL_WIDTH * real_total_length
    real_efficiency = 100 * total_area_demand / total_area_used if total_area_used else 0.0

    lines = [
        f"切割报告  Sheet{sheet_num}  解码方式: {decoder_mode}",
        "=" * 72,
        "",
        "二、方案总览",
        "",
        f"母板宽度: {PANEL_WIDTH} mm",
        f"总消耗长度: {int(real_total_length)} mm",
        f"材料利用率: {real_efficiency:.2f}%",
        f"编码条带数: {solution['num_strips']}",
        f"还原后条带数/阶段数: {int(solution['num_strips'] * SCALE_FACTOR) if decoder_mode != 'stage_based' else len(solution['strips'])}",
    ]

    if any(int(num) % SCALE_FACTOR != 0 for num in demand["num"]):
        lines.extend(
            [
                "",
                "注意：当前实验启用了数量缩放求解。",
                f"缩放因子为 {SCALE_FACTOR}，若订单数量不是 {SCALE_FACTOR} 的整数倍，",
                "以下产出数量按缩放结果还原，实际落地时请对余数单独补切。",
            ]
        )

    return lines


def _build_compact_mode_section(strips, repeat_counts):
    lines = ["", "三、切割执行说明", ""]
    produced_totals = defaultdict(int)

    for idx, (strip, repeat_count) in enumerate(zip(strips, repeat_counts), start=1):
        actual_repeat = repeat_count * SCALE_FACTOR
        groups = _collect_lane_groups(strip)
        used_width = sum(group["width"] * group["lane_count"] for group in groups)
        waste_width = PANEL_WIDTH - used_width

        lines.append(f"模式 {idx}")
        lines.append(f"1. 本模式连续切 {int(actual_repeat)} 条。")
        lines.append(f"2. 每条母板长度 {int(strip.strip_length)} mm。")
        lines.append(f"3. 刀位宽度组合: {_format_width_combo(groups)} = {int(used_width)} mm，余宽 {int(waste_width)} mm。")
        lines.append(f"4. 刀位累计位置（从左到右）: {_format_knife_positions(groups)} mm。")
        lines.append("5. 各刀道执行明细：")

        for lane_no, group in enumerate(groups, start=1):
            lane_total = actual_repeat * group["lane_count"]
            tail_length = max(0, int(strip.strip_length - group["length"]))
            produced_totals[group["type_id"]] += lane_total
            lines.append(
                "   "
                f"- 刀道组 {lane_no}: T{group['type_id'] + 1}，共 {group['lane_count']} 道；"
                f"每道宽 {int(group['width'])} mm，定尺 {int(group['length'])} mm；"
                f"每条母板每道出 1 件，连续切 {int(actual_repeat)} 条后，共出 {int(lane_total)} 件；"
                f"单道尾料 {tail_length} mm。"
            )

        lines.append("")

    return lines, produced_totals


def _build_stage_mode_section(strips):
    lines = ["", "三、切割执行说明", ""]
    produced_totals = defaultdict(int)

    for idx, strip in enumerate(strips, start=1):
        actual_stage_length = strip.strip_length * SCALE_FACTOR
        groups = _collect_lane_groups(strip)
        used_width = sum(group["width"] * group["lane_count"] for group in groups)
        waste_width = PANEL_WIDTH - used_width

        lines.append(f"阶段 {idx}")
        lines.append(f"1. 本阶段按同一组刀位连续走料 {int(actual_stage_length)} mm。")
        lines.append(f"2. 刀位宽度组合: {_format_width_combo(groups)} = {int(used_width)} mm，余宽 {int(waste_width)} mm。")
        lines.append(f"3. 刀位累计位置（从左到右）: {_format_knife_positions(groups)} mm。")
        lines.append("4. 各刀道执行明细：")

        for lane_no, group in enumerate(groups, start=1):
            pieces_per_lane = actual_stage_length // group["length"]
            lane_total = pieces_per_lane * group["lane_count"]
            tail_length = actual_stage_length - pieces_per_lane * group["length"]
            produced_totals[group["type_id"]] += lane_total
            lines.append(
                "   "
                f"- 刀道组 {lane_no}: T{group['type_id'] + 1}，共 {group['lane_count']} 道；"
                f"每道宽 {int(group['width'])} mm，定尺 {int(group['length'])} mm；"
                f"单道可切 {int(pieces_per_lane)} 件，阶段合计 {int(lane_total)} 件；"
                f"单道尾料 {int(tail_length)} mm。"
            )

        lines.append("")

    return lines, produced_totals


def _format_total_section(demand, produced_totals):
    lines = ["四、产出核对", ""]
    for idx, demand_num in enumerate(demand["num"], start=1):
        produced = int(produced_totals.get(idx - 1, 0))
        gap = produced - int(demand_num)
        if gap == 0:
            gap_text = "与订单一致"
        elif gap > 0:
            gap_text = f"比订单多 {gap} 件"
        else:
            gap_text = f"比订单少 {abs(gap)} 件"
        lines.append(
            f"T{idx}: 订单 {int(demand_num)} 件，报告产出 {produced} 件，{gap_text}"
        )

    lines.extend(
        [
            "",
            "五、车间执行提示",
            "",
            "1. 请严格按报告中的模式/阶段顺序执行，不要随意交换顺序。",
            "2. 每切完一个模式或阶段，请现场核对对应产品累计产量，避免重复切或漏切。",
            "3. 若订单数量与报告产量存在少量差异，通常是缩放求解造成的余数问题，应单独补切尾单。",
            "4. 现场如需换刀，请优先在模式或阶段切换点进行，避免中途打断当前组合。",
        ]
    )
    return lines


def build_cutting_report_text(sheet_num, decoder_mode, demand, solution):
    lines = []
    lines.extend(_format_summary_section(sheet_num, decoder_mode, demand, solution))
    lines.append("")
    lines.extend(_format_demand_section(demand))

    if decoder_mode == "stage_based":
        detail_lines, produced_totals = _build_stage_mode_section(solution["strips"])
    else:
        merged_strips, repeat_counts = merge_same_pattern_strips(solution["strips"])
        detail_lines, produced_totals = _build_compact_mode_section(merged_strips, repeat_counts)

    lines.extend(detail_lines)
    lines.append("")
    lines.extend(_format_total_section(demand, produced_totals))
    lines.append("")
    return "\n".join(lines)


def write_cutting_report(sheet_num, decoder_mode, demand, solution, output_path):
    output_path = Path(output_path)
    output_path.write_text(
        build_cutting_report_text(sheet_num, decoder_mode, demand, solution),
        encoding="utf-8",
    )
    return output_path
