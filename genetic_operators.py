# -*- coding: utf-8 -*-
"""
遗传操作模块 - 选择、交叉、变异
"""

import random
from config import TOURNAMENT_SIZE, CROSSOVER_RATE, MUTATION_RATE


def tournament_selection(population, fitness_values, tournament_size=TOURNAMENT_SIZE):
    """
    锦标赛选择
    
    参数:
        population: list，种群（染色体列表）
        fitness_values: list，适应度值列表
        tournament_size: int，锦标赛参与者数量
    
    返回:
        selected: 选中的个体
    """
    # 随机选择tournament_size个个体
    candidates_idx = random.sample(range(len(population)), tournament_size)
    
    # 选择适应度最好的（值最小的）
    best_idx = min(candidates_idx, key=lambda i: fitness_values[i])
    
    return population[best_idx].copy()


def order_crossover(parent1, parent2):
    """
    顺序交叉 (OX - Order Crossover)
    适用于排列编码的染色体
    
    参数:
        parent1, parent2: list，两个父代染色体
    
    返回:
        child1, child2: 两个子代染色体
    """
    size = len(parent1)
    
    # 随机选择两个交叉点
    point1 = random.randint(0, size - 2)
    point2 = random.randint(point1 + 1, size - 1)
    
    # 创建子代
    child1 = [-1] * size
    child2 = [-1] * size
    
    # 复制交叉段
    child1[point1:point2+1] = parent1[point1:point2+1]
    child2[point1:point2+1] = parent2[point1:point2+1]
    
    # 填充剩余位置
    def fill_remaining(child, parent, point1, point2):
        # 获取child中已有的元素
        existing = set(child[point1:point2+1])
        # 从parent中获取不在existing中的元素，按顺序
        remaining = [x for x in parent if x not in existing]
        
        # 填充
        j = 0
        for i in range(size):
            if child[i] == -1:
                child[i] = remaining[j]
                j += 1
    
    fill_remaining(child1, parent2, point1, point2)
    fill_remaining(child2, parent1, point1, point2)
    
    return child1, child2


def pmx_crossover(parent1, parent2):
    """
    部分匹配交叉 (PMX - Partially Matched Crossover)
    
    参数:
        parent1, parent2: list，两个父代染色体
    
    返回:
        child1, child2: 两个子代染色体
    """
    size = len(parent1)
    
    # 随机选择两个交叉点
    point1 = random.randint(0, size - 2)
    point2 = random.randint(point1 + 1, size - 1)
    
    def pmx_single(p1, p2):
        child = [-1] * size
        
        # 复制交叉段
        child[point1:point2+1] = p1[point1:point2+1]
        
        # 建立映射关系
        mapping = {}
        for i in range(point1, point2 + 1):
            mapping[p1[i]] = p2[i]
        
        # 填充剩余位置
        for i in range(size):
            if i < point1 or i > point2:
                val = p2[i]
                while val in child[point1:point2+1]:
                    val = mapping.get(val, val)
                child[i] = val
        
        return child
    
    child1 = pmx_single(parent1, parent2)
    child2 = pmx_single(parent2, parent1)
    
    return child1, child2


def swap_mutation(individual):
    """
    交换变异：随机选择两个位置交换
    
    参数:
        individual: list，染色体
    
    返回:
        mutated: 变异后的染色体
    """
    mutated = individual.copy()
    size = len(mutated)
    
    # 随机选择两个不同位置
    i, j = random.sample(range(size), 2)
    
    # 交换
    mutated[i], mutated[j] = mutated[j], mutated[i]
    
    return mutated


def insert_mutation(individual):
    """
    插入变异：随机选择一个元素插入到另一个位置
    
    参数:
        individual: list，染色体
    
    返回:
        mutated: 变异后的染色体
    """
    mutated = individual.copy()
    size = len(mutated)
    
    # 随机选择两个位置
    i = random.randint(0, size - 1)
    j = random.randint(0, size - 1)
    
    if i != j:
        # 取出元素
        elem = mutated.pop(i)
        # 插入到新位置
        mutated.insert(j, elem)
    
    return mutated


def inversion_mutation(individual):
    """
    逆转变异：随机选择一段反转
    
    参数:
        individual: list，染色体
    
    返回:
        mutated: 变异后的染色体
    """
    mutated = individual.copy()
    size = len(mutated)
    
    # 随机选择两个位置
    i = random.randint(0, size - 2)
    j = random.randint(i + 1, size - 1)
    
    # 反转该段
    mutated[i:j+1] = reversed(mutated[i:j+1])
    
    return mutated


def mutate(individual, mutation_type='mixed'):
    """
    变异操作
    
    参数:
        individual: list，染色体
        mutation_type: str，变异类型 ('swap', 'insert', 'inversion', 'mixed')
    
    返回:
        mutated: 变异后的染色体
    """
    if mutation_type == 'swap':
        return swap_mutation(individual)
    elif mutation_type == 'insert':
        return insert_mutation(individual)
    elif mutation_type == 'inversion':
        return inversion_mutation(individual)
    elif mutation_type == 'mixed':
        # 随机选择一种变异方式
        mutation_func = random.choice([swap_mutation, insert_mutation, inversion_mutation])
        return mutation_func(individual)
    else:
        return swap_mutation(individual)


def crossover(parent1, parent2, crossover_type='ox'):
    """
    交叉操作
    
    参数:
        parent1, parent2: list，两个父代
        crossover_type: str，交叉类型 ('ox', 'pmx')
    
    返回:
        child1, child2: 两个子代
    """
    if crossover_type == 'ox':
        return order_crossover(parent1, parent2)
    elif crossover_type == 'pmx':
        return pmx_crossover(parent1, parent2)
    else:
        return order_crossover(parent1, parent2)


if __name__ == "__main__":
    # 测试遗传操作
    import random
    
    # 创建测试染色体
    size = 10
    parent1 = list(range(size))
    parent2 = list(range(size))
    random.shuffle(parent1)
    random.shuffle(parent2)
    
    print(f"Parent 1: {parent1}")
    print(f"Parent 2: {parent2}")
    
    # 测试交叉
    child1, child2 = order_crossover(parent1, parent2)
    print(f"\nOX Crossover:")
    print(f"Child 1: {child1}")
    print(f"Child 2: {child2}")
    
    # 验证子代合法性
    print(f"Child 1 valid: {sorted(child1) == list(range(size))}")
    print(f"Child 2 valid: {sorted(child2) == list(range(size))}")
    
    # 测试变异
    print(f"\nMutations on Parent 1:")
    print(f"Swap: {swap_mutation(parent1)}")
    print(f"Insert: {insert_mutation(parent1)}")
    print(f"Inversion: {inversion_mutation(parent1)}")
