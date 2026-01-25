# -*- coding: utf-8 -*-
"""
遗传算法引擎
"""

import random
import time
from config import (
    POPULATION_SIZE, MAX_GENERATIONS, 
    CROSSOVER_RATE, MUTATION_RATE, ELITE_SIZE, RANDOM_SEED
)
from decoder import calculate_fitness, decode, decode_hybrid, calculate_efficiency
from genetic_operators import tournament_selection, crossover, mutate


class GeneticAlgorithm:
    """遗传算法类"""
    
    def __init__(self, items, population_size=POPULATION_SIZE, 
                 max_generations=MAX_GENERATIONS,
                 crossover_rate=CROSSOVER_RATE,
                 mutation_rate=MUTATION_RATE,
                 elite_size=ELITE_SIZE):
        """
        初始化遗传算法
        
        参数:
            items: list of Item，所有小板列表
            population_size: int，种群大小
            max_generations: int，最大迭代代数
            crossover_rate: float，交叉概率
            mutation_rate: float，变异概率
            elite_size: int，精英保留数量
        """
        self.items = items
        self.num_items = len(items)
        self.population_size = population_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        
        # 记录进化历史
        self.history = {
            'best_fitness': [],
            'avg_fitness': [],
            'best_individual': None
        }
        
        # 设置随机种子
        if RANDOM_SEED is not None:
            random.seed(RANDOM_SEED)
    
    def initialize_population(self):
        """
        初始化种群
        
        返回:
            population: list，初始种群
        """
        population = []
        base = list(range(self.num_items))
        
        for _ in range(self.population_size):
            individual = base.copy()
            random.shuffle(individual)
            population.append(individual)
        
        return population
    
    def initialize_population_greedy(self):
        """
        使用贪心策略初始化种群（部分个体）
        将相近宽度和长度的板子放在一起，提高初始解的质量
        
        返回:
            population: list，初始种群
        """
        population = []
        base = list(range(self.num_items))
        
        # 一部分使用贪心策略
        greedy_count = self.population_size // 3
        
        # 策略1：按宽度排序（尽量把宽度能凑满的放一起）
        sorted_by_width = sorted(base, key=lambda i: self.items[i].width)
        population.append(sorted_by_width.copy())
        
        # 策略2：按长度排序（减少长度方向的浪费）
        sorted_by_length = sorted(base, key=lambda i: self.items[i].length)
        population.append(sorted_by_length.copy())
        
        # 策略3：按长度降序排序
        sorted_by_length_desc = sorted(base, key=lambda i: -self.items[i].length)
        population.append(sorted_by_length_desc.copy())
        
        # 策略4：按宽度分组，组内按长度排序
        sorted_by_width_then_length = sorted(base, key=lambda i: (self.items[i].width, self.items[i].length))
        population.append(sorted_by_width_then_length.copy())
        
        # 策略5：按类型分组（同类型放一起）
        sorted_by_type = sorted(base, key=lambda i: (self.items[i].type_id, self.items[i].length))
        population.append(sorted_by_type.copy())
        
        # 策略6：先长度后宽度
        sorted_by_length_then_width = sorted(base, key=lambda i: (self.items[i].length, self.items[i].width))
        population.append(sorted_by_length_then_width.copy())
        
        # 策略7-N：贪心基础上局部打乱
        for _ in range(greedy_count - 6):
            individual = sorted_by_length.copy()
            # 局部打乱（只在小范围内交换）
            chunk_size = max(5, self.num_items // 20)
            for i in range(0, len(individual), chunk_size):
                chunk = individual[i:i+chunk_size]
                random.shuffle(chunk)
                individual[i:i+chunk_size] = chunk
            population.append(individual)
        
        # 剩余使用随机初始化
        for _ in range(self.population_size - len(population)):
            individual = base.copy()
            random.shuffle(individual)
            population.append(individual)
        
        return population
    
    def evaluate_population(self, population):
        """
        评估种群中所有个体的适应度
        
        参数:
            population: list，种群
        
        返回:
            fitness_values: list，适应度值列表
        """
        fitness_values = []
        for individual in population:
            fitness = calculate_fitness(individual, self.items)
            fitness_values.append(fitness)
        return fitness_values
    
    def local_search_2opt(self, individual, max_iterations=50):
        """
        2-opt局部搜索：尝试交换片段来改进解
        """
        best = individual.copy()
        best_fitness = calculate_fitness(best, self.items)
        improved = True
        iterations = 0
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            # 随机选择一些位置进行2-opt
            positions = random.sample(range(len(best)), min(20, len(best)))
            
            for i in positions:
                for j in positions:
                    if i >= j:
                        continue
                    # 反转i到j之间的片段
                    new_individual = best.copy()
                    new_individual[i:j+1] = reversed(new_individual[i:j+1])
                    
                    new_fitness = calculate_fitness(new_individual, self.items)
                    if new_fitness < best_fitness:
                        best = new_individual
                        best_fitness = new_fitness
                        improved = True
                        break
                if improved:
                    break
        
        return best, best_fitness
    
    def local_search_swap(self, individual, max_iterations=30):
        """
        交换局部搜索：尝试交换不同类型的板子位置
        """
        best = individual.copy()
        best_fitness = calculate_fitness(best, self.items)
        
        for _ in range(max_iterations):
            # 随机选择两个不同类型的位置交换
            i, j = random.sample(range(len(best)), 2)
            
            if self.items[best[i]].type_id != self.items[best[j]].type_id:
                new_individual = best.copy()
                new_individual[i], new_individual[j] = new_individual[j], new_individual[i]
                
                new_fitness = calculate_fitness(new_individual, self.items)
                if new_fitness < best_fitness:
                    best = new_individual
                    best_fitness = new_fitness
        
        return best, best_fitness
    
    def local_search_block_move(self, individual, max_iterations=20):
        """
        块移动局部搜索：尝试移动一块连续的板子到其他位置
        """
        best = individual.copy()
        best_fitness = calculate_fitness(best, self.items)
        
        for _ in range(max_iterations):
            # 随机选择一个块
            block_size = random.randint(2, min(10, len(best) // 4))
            start = random.randint(0, len(best) - block_size)
            # 随机选择新位置
            new_pos = random.randint(0, len(best) - block_size)
            
            if new_pos != start:
                new_individual = best.copy()
                block = new_individual[start:start+block_size]
                del new_individual[start:start+block_size]
                
                # 调整插入位置
                if new_pos > start:
                    new_pos -= block_size
                new_individual[new_pos:new_pos] = block
                
                new_fitness = calculate_fitness(new_individual, self.items)
                if new_fitness < best_fitness:
                    best = new_individual
                    best_fitness = new_fitness
        
        return best, best_fitness

    def evolve(self, verbose=True):
        """
        执行遗传算法进化
        
        参数:
            verbose: bool，是否打印进度信息
        
        返回:
            best_individual: list，最优个体
            best_fitness: float，最优适应度
        """
        start_time = time.time()
        
        # 初始化种群（使用贪心策略）
        population = self.initialize_population_greedy()
        
        # 评估初始种群
        fitness_values = self.evaluate_population(population)
        
        # 记录最优
        best_idx = fitness_values.index(min(fitness_values))
        best_individual = population[best_idx].copy()
        best_fitness = fitness_values[best_idx]
        
        if verbose:
            print(f"初始最优适应度: {best_fitness:.2f}")
        
        # 进化循环
        for generation in range(self.max_generations):
            new_population = []
            
            # 精英保留
            elite_indices = sorted(range(len(fitness_values)), 
                                   key=lambda i: fitness_values[i])[:self.elite_size]
            for idx in elite_indices:
                new_population.append(population[idx].copy())
            
            # 生成新个体
            while len(new_population) < self.population_size:
                # 选择父代
                parent1 = tournament_selection(population, fitness_values)
                parent2 = tournament_selection(population, fitness_values)
                
                # 交叉
                if random.random() < self.crossover_rate:
                    child1, child2 = crossover(parent1, parent2, 'ox')
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                # 变异
                if random.random() < self.mutation_rate:
                    child1 = mutate(child1, 'mixed')
                if random.random() < self.mutation_rate:
                    child2 = mutate(child2, 'mixed')
                
                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            
            # 更新种群
            population = new_population
            fitness_values = self.evaluate_population(population)
            
            # 更新最优
            gen_best_idx = fitness_values.index(min(fitness_values))
            gen_best_fitness = fitness_values[gen_best_idx]
            
            if gen_best_fitness < best_fitness:
                best_fitness = gen_best_fitness
                best_individual = population[gen_best_idx].copy()
            
            # 每隔一定代数进行局部搜索优化最优个体
            if (generation + 1) % 20 == 0:
                # 对当前最优个体进行局部搜索
                ls_individual, ls_fitness = self.local_search_2opt(best_individual, max_iterations=30)
                if ls_fitness < best_fitness:
                    best_fitness = ls_fitness
                    best_individual = ls_individual
                    # 将改进的个体放入种群
                    worst_idx = fitness_values.index(max(fitness_values))
                    population[worst_idx] = best_individual.copy()
                    fitness_values[worst_idx] = best_fitness
                
                # 也尝试交换搜索
                ls_individual2, ls_fitness2 = self.local_search_swap(best_individual, max_iterations=30)
                if ls_fitness2 < best_fitness:
                    best_fitness = ls_fitness2
                    best_individual = ls_individual2
            
            # 自适应变异率：如果长时间没改进，增加变异
            if generation > 20 and len(self.history['best_fitness']) > 20:
                recent_best = self.history['best_fitness'][-20:]
                if max(recent_best) == min(recent_best):  # 20代没改进
                    self.mutation_rate = min(0.5, self.mutation_rate * 1.1)
                else:
                    self.mutation_rate = max(0.15, self.mutation_rate * 0.95)
            
            # 记录历史
            self.history['best_fitness'].append(best_fitness)
            self.history['avg_fitness'].append(sum(fitness_values) / len(fitness_values))
            
            # 打印进度
            if verbose and (generation + 1) % 10 == 0:
                elapsed = time.time() - start_time
                print(f"Generation {generation + 1}/{self.max_generations}: "
                      f"Best = {best_fitness:.2f}, "
                      f"Avg = {self.history['avg_fitness'][-1]:.2f}, "
                      f"Time = {elapsed:.1f}s")
        
        self.history['best_individual'] = best_individual
        
        # 最终阶段：对最优解进行强化局部搜索
        if verbose:
            print("\n正在进行最终局部搜索优化...")
        
        for _ in range(3):  # 多轮局部搜索
            improved = False
            
            ls_individual, ls_fitness = self.local_search_2opt(best_individual, max_iterations=100)
            if ls_fitness < best_fitness:
                best_fitness = ls_fitness
                best_individual = ls_individual
                improved = True
            
            ls_individual, ls_fitness = self.local_search_swap(best_individual, max_iterations=50)
            if ls_fitness < best_fitness:
                best_fitness = ls_fitness
                best_individual = ls_individual
                improved = True
            
            ls_individual, ls_fitness = self.local_search_block_move(best_individual, max_iterations=50)
            if ls_fitness < best_fitness:
                best_fitness = ls_fitness
                best_individual = ls_individual
                improved = True
            
            if not improved:
                break
        
        self.history['best_individual'] = best_individual
        self.history['best_fitness'].append(best_fitness)
        
        total_time = time.time() - start_time
        if verbose:
            print(f"\n进化完成! 总耗时: {total_time:.2f}s")
            print(f"最优适应度: {best_fitness:.2f}")
        
        return best_individual, best_fitness
    
    def get_solution(self, individual=None):
        """
        获取解码后的解决方案
        
        参数:
            individual: list，染色体（默认使用最优个体）
        
        返回:
            solution: dict，包含切割方案的详细信息
        """
        if individual is None:
            individual = self.history['best_individual']
        
        if individual is None:
            raise ValueError("没有可用的解，请先运行evolve()")
        
        # 使用混合解码器获取最优结果
        total_length, strips, penalty = decode_hybrid(individual, self.items)
        efficiency = calculate_efficiency(total_length, self.items)
        
        solution = {
            'total_length': total_length,
            'penalty': penalty,
            'efficiency': efficiency,
            'num_strips': len(strips),
            'strips': strips,
            'individual': individual
        }
        
        return solution


if __name__ == "__main__":
    # 测试遗传算法
    from data_loader import load_demand_from_excel, expand_demand
    
    # 加载数据
    demand = load_demand_from_excel(sheet_num=1)
    items, type_info = expand_demand(demand)
    
    print(f"总共 {len(items)} 个小板待切割")
    print(f"产品类型信息:")
    print(type_info)
    print()
    
    # 创建并运行遗传算法
    ga = GeneticAlgorithm(
        items,
        population_size=50,
        max_generations=100,
        crossover_rate=0.8,
        mutation_rate=0.2
    )
    
    best_individual, best_fitness = ga.evolve(verbose=True)
    
    # 获取解决方案
    solution = ga.get_solution()
    
    print(f"\n最终解决方案:")
    print(f"总切割长度: {solution['total_length']:.2f}")
    print(f"材料利用率: {solution['efficiency']:.2f}%")
    print(f"切割条数: {solution['num_strips']}")
