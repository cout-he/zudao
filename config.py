# -*- coding: utf-8 -*-
"""
遗传算法配置参数
"""

# 钢板参数
PANEL_WIDTH = 1250          # 大板宽度 (mm)
MIN_CUT_GAP = 200           # 最小纵切距离约束 (mm)

# 遗传算法参数
POPULATION_SIZE = 80        # 种群大小
MAX_GENERATIONS = 200       # 最大迭代代数
CROSSOVER_RATE = 0.85       # 交叉概率
MUTATION_RATE = 0.2         # 变异概率
TOURNAMENT_SIZE = 3         # 锦标赛选择的参与者数量
ELITE_SIZE = 5              # 精英保留数量

# 惩罚参数
PENALTY_VALUE = 100000      # 违反约束时的惩罚值

# 数据缩放（如果数量太大，可以缩小比例）
# 设为2表示每2个同类板编码为1个（精度更高）
SCALE_FACTOR = 2            # 缩放因子

# 随机种子（可选，用于复现结果）
RANDOM_SEED = None          # 设为None则每次随机
