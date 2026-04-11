# -*- coding: utf-8 -*-
"""
遗传算法配置参数
"""

# 钢板参数
PANEL_WIDTH = 1250          # 大板宽度 (mm)
MIN_CUT_GAP = 200           # 最小纵切距离约束 (mm)

# 遗传算法参数
POPULATION_SIZE = 24        # 种群大小
MAX_GENERATIONS = 60        # 最大迭代代数
CROSSOVER_RATE = 0.85       # 交叉概率
MUTATION_RATE = 0.22        # 变异概率
TOURNAMENT_SIZE = 3         # 锦标赛选择的参与者数量
ELITE_SIZE = 3              # 精英保留数量

# 惩罚参数
PENALTY_VALUE = 100000      # 违反约束时的惩罚值

# 数据缩放（如果数量太大，可以缩小比例）
# 设为4表示每4个同类板编码为1个，速度和精度更均衡
SCALE_FACTOR = 4            # 缩放因子

# 解码与搜索策略
DECODER_MODE = 'best_fit'   # 可选: simple, best_fit, length_priority, hybrid
ENABLE_LOCAL_SEARCH = True  # 是否启用局部搜索
LOCAL_SEARCH_INTERVAL = 30  # 每隔多少代尝试一次局部搜索
LOCAL_SEARCH_STEPS = 12     # 单次局部搜索尝试次数
FINAL_LOCAL_SEARCH_ROUNDS = 1
EARLY_STOPPING_PATIENCE = 35

# ---------------------------------------------------------------------------
# Clean overrides used by the current implementation.
# These definitions are appended so they override the garbled legacy lines.
# ---------------------------------------------------------------------------
PANEL_WIDTH = 1250
MIN_CUT_GAP = 200
VERTICAL_CUT_INCLUSIVE = True

POPULATION_SIZE = 24
MAX_GENERATIONS = 60
CROSSOVER_RATE = 0.85
MUTATION_RATE = 0.22
TOURNAMENT_SIZE = 3
ELITE_SIZE = 3

PENALTY_VALUE = 100000
SCALE_FACTOR = 3

DECODER_MODE = 'stage_based'
ENABLE_LOCAL_SEARCH = True
LOCAL_SEARCH_INTERVAL = 30
LOCAL_SEARCH_STEPS = 12
FINAL_LOCAL_SEARCH_ROUNDS = 1
EARLY_STOPPING_PATIENCE = 35
PATTERN_TOP_CANDIDATES = 16
PATTERN_MIN_SAVINGS = -20.0

RANDOM_SEED = 42

# 随机种子（可选，用于复现结果）
RANDOM_SEED = 42            # 固定随机种子便于复现
