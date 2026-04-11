# -*- coding: utf-8 -*-
"""
快速版遗传算法引擎
"""

import random
import time

from core.config import (
    POPULATION_SIZE, MAX_GENERATIONS,
    CROSSOVER_RATE, MUTATION_RATE, ELITE_SIZE, RANDOM_SEED,
    DECODER_MODE, ENABLE_LOCAL_SEARCH, LOCAL_SEARCH_INTERVAL,
    LOCAL_SEARCH_STEPS, FINAL_LOCAL_SEARCH_ROUNDS, EARLY_STOPPING_PATIENCE,
)
from core.decoder import calculate_fitness, decode_by_mode, calculate_efficiency
from core.genetic_operators import tournament_selection, crossover, mutate


class GeneticAlgorithm:
    """更适合大规模实例的快速遗传算法。"""

    def __init__(
        self,
        items,
        population_size=POPULATION_SIZE,
        max_generations=MAX_GENERATIONS,
        crossover_rate=CROSSOVER_RATE,
        mutation_rate=MUTATION_RATE,
        elite_size=ELITE_SIZE,
        decoder_mode=DECODER_MODE,
    ):
        self.items = items
        self.num_items = len(items)
        self.population_size = population_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.decoder_mode = decoder_mode

        self.history = {
            "best_fitness": [],
            "avg_fitness": [],
            "best_individual": None,
        }

        if RANDOM_SEED is not None:
            random.seed(RANDOM_SEED)

    def _fitness(self, individual):
        return calculate_fitness(individual, self.items, self.decoder_mode)

    def initialize_population_greedy(self):
        population = []
        base = list(range(self.num_items))
        greedy_count = max(6, self.population_size // 3)

        seed_individuals = [
            sorted(base, key=lambda i: self.items[i].width),
            sorted(base, key=lambda i: self.items[i].length),
            sorted(base, key=lambda i: -self.items[i].length),
            sorted(base, key=lambda i: (self.items[i].type_id, self.items[i].length)),
            sorted(base, key=lambda i: (self.items[i].width, self.items[i].length)),
            sorted(base, key=lambda i: (self.items[i].length, self.items[i].width)),
        ]

        for individual in seed_individuals[:greedy_count]:
            population.append(individual.copy())

        while len(population) < greedy_count:
            individual = seed_individuals[1].copy()
            chunk_size = max(5, self.num_items // 20)
            for start in range(0, len(individual), chunk_size):
                chunk = individual[start:start + chunk_size]
                random.shuffle(chunk)
                individual[start:start + chunk_size] = chunk
            population.append(individual)

        while len(population) < self.population_size:
            individual = base.copy()
            random.shuffle(individual)
            population.append(individual)

        return population

    def evaluate_population(self, population):
        return [self._fitness(individual) for individual in population]

    def local_search_swap(self, individual, max_iterations=30):
        best = individual.copy()
        best_fitness = self._fitness(best)

        for _ in range(max_iterations):
            i, j = random.sample(range(len(best)), 2)
            if self.items[best[i]].type_id == self.items[best[j]].type_id:
                continue

            candidate = best.copy()
            candidate[i], candidate[j] = candidate[j], candidate[i]
            candidate_fitness = self._fitness(candidate)
            if candidate_fitness < best_fitness:
                best = candidate
                best_fitness = candidate_fitness

        return best, best_fitness

    def local_search_block_move(self, individual, max_iterations=20):
        best = individual.copy()
        best_fitness = self._fitness(best)

        for _ in range(max_iterations):
            block_size = random.randint(2, min(8, max(2, len(best) // 8)))
            start = random.randint(0, len(best) - block_size)
            new_pos = random.randint(0, len(best) - block_size)
            if new_pos == start:
                continue

            candidate = best.copy()
            block = candidate[start:start + block_size]
            del candidate[start:start + block_size]
            if new_pos > start:
                new_pos -= block_size
            candidate[new_pos:new_pos] = block

            candidate_fitness = self._fitness(candidate)
            if candidate_fitness < best_fitness:
                best = candidate
                best_fitness = candidate_fitness

        return best, best_fitness

    def _run_light_local_search(self, best_individual, best_fitness):
        improved = False

        candidate, candidate_fitness = self.local_search_swap(
            best_individual, max_iterations=LOCAL_SEARCH_STEPS
        )
        if candidate_fitness < best_fitness:
            best_individual = candidate
            best_fitness = candidate_fitness
            improved = True

        candidate, candidate_fitness = self.local_search_block_move(
            best_individual, max_iterations=max(4, LOCAL_SEARCH_STEPS // 2)
        )
        if candidate_fitness < best_fitness:
            best_individual = candidate
            best_fitness = candidate_fitness
            improved = True

        return best_individual, best_fitness, improved

    def evolve(self, verbose=True):
        start_time = time.time()
        population = self.initialize_population_greedy()
        fitness_values = self.evaluate_population(population)

        best_idx = fitness_values.index(min(fitness_values))
        best_individual = population[best_idx].copy()
        best_fitness = fitness_values[best_idx]
        stagnant_generations = 0

        if verbose:
            print(f"初始最优适应度: {best_fitness:.2f}")

        for generation in range(self.max_generations):
            new_population = []

            elite_indices = sorted(
                range(len(fitness_values)),
                key=lambda i: fitness_values[i]
            )[:self.elite_size]
            for idx in elite_indices:
                new_population.append(population[idx].copy())

            while len(new_population) < self.population_size:
                parent1 = tournament_selection(population, fitness_values)
                parent2 = tournament_selection(population, fitness_values)

                if random.random() < self.crossover_rate:
                    child1, child2 = crossover(parent1, parent2, "ox")
                else:
                    child1, child2 = parent1.copy(), parent2.copy()

                if random.random() < self.mutation_rate:
                    child1 = mutate(child1, "mixed")
                if random.random() < self.mutation_rate:
                    child2 = mutate(child2, "mixed")

                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)

            population = new_population
            fitness_values = self.evaluate_population(population)

            gen_best_idx = fitness_values.index(min(fitness_values))
            gen_best_fitness = fitness_values[gen_best_idx]

            if gen_best_fitness < best_fitness:
                best_fitness = gen_best_fitness
                best_individual = population[gen_best_idx].copy()
                stagnant_generations = 0
            else:
                stagnant_generations += 1

            if ENABLE_LOCAL_SEARCH and (generation + 1) % LOCAL_SEARCH_INTERVAL == 0:
                best_individual, best_fitness, improved = self._run_light_local_search(
                    best_individual, best_fitness
                )
                if improved:
                    stagnant_generations = 0
                    worst_idx = fitness_values.index(max(fitness_values))
                    population[worst_idx] = best_individual.copy()
                    fitness_values[worst_idx] = best_fitness

            if generation > 20 and len(self.history["best_fitness"]) > 20:
                recent_best = self.history["best_fitness"][-20:]
                if max(recent_best) == min(recent_best):
                    self.mutation_rate = min(0.4, self.mutation_rate * 1.05)
                else:
                    self.mutation_rate = max(0.15, self.mutation_rate * 0.98)

            self.history["best_fitness"].append(best_fitness)
            self.history["avg_fitness"].append(sum(fitness_values) / len(fitness_values))

            if verbose and (generation + 1) % 10 == 0:
                elapsed = time.time() - start_time
                print(
                    f"Generation {generation + 1}/{self.max_generations}: "
                    f"Best = {best_fitness:.2f}, "
                    f"Avg = {self.history['avg_fitness'][-1]:.2f}, "
                    f"Time = {elapsed:.1f}s"
                )

            if stagnant_generations >= EARLY_STOPPING_PATIENCE:
                if verbose:
                    print(
                        f"Early stopping at generation {generation + 1}: "
                        f"{EARLY_STOPPING_PATIENCE} generations without improvement."
                    )
                break

        if ENABLE_LOCAL_SEARCH and FINAL_LOCAL_SEARCH_ROUNDS > 0:
            if verbose:
                print("\n正在进行最终局部搜索优化..")
            for _ in range(FINAL_LOCAL_SEARCH_ROUNDS):
                best_individual, best_fitness, improved = self._run_light_local_search(
                    best_individual, best_fitness
                )
                if not improved:
                    break

        self.history["best_individual"] = best_individual
        self.history["best_fitness"].append(best_fitness)

        total_time = time.time() - start_time
        if verbose:
            print(f"\n进化完成! 总耗时: {total_time:.2f}s")
            print(f"最优适应度: {best_fitness:.2f}")

        return best_individual, best_fitness

    def get_solution(self, individual=None):
        if individual is None:
            individual = self.history["best_individual"]

        if individual is None:
            raise ValueError("没有可用的解，请先运行 evolve()")

        total_length, strips, penalty = decode_by_mode(individual, self.items, self.decoder_mode)
        efficiency = calculate_efficiency(total_length, self.items)

        return {
            "total_length": total_length,
            "penalty": penalty,
            "efficiency": efficiency,
            "num_strips": len(strips),
            "strips": strips,
            "individual": individual,
        }
