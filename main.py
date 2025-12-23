# MusicAndMath/main.py
import random
import config
import utils
from fitness_function import get_fitness

def op_micro_adjust(melody):
    """微调：上下移动 1-2 个半音"""
    if len(melody) == 0: return melody
    idx = random.randint(0, len(melody)-1)
    if melody[idx] > 0:
        shift = random.choice([-2, -1, 1, 2])
        new_val = melody[idx] + shift
        # 确保在调内更好
        if config.PITCH_MIN <= new_val <= config.PITCH_MAX:
            melody[idx] = new_val
    return melody

def op_transpose(melody):
    """移调：整体将旋律升高或降低"""
    # 常用移调间隔：-12, -7 (下五度), -5 (下四度), -2, +2, +5, +7, +12
    shift = random.choice([-12, -7, -5, -2, 2, 5, 7, 12])
    new_melody = melody[:]
    for i in range(len(new_melody)):
        if new_melody[i] > 0:
            val = new_melody[i] + shift
            if config.PITCH_MIN <= val <= config.PITCH_MAX:
                new_melody[i] = val
            else:
                # 如果超界，就不移了，或者八度反转，这里简单处理为不移
                new_melody[i] = new_melody[i] 
    return new_melody

def op_smooth_contour(melody):
    """平滑：解决锯齿纹样"""
    # 如果检测到 60 -> 72 -> 60 这种剧烈跳动，试图将中间值拉平
    for i in range(1, len(melody)-1):
        prev_n = melody[i-1]
        curr_n = melody[i]
        next_n = melody[i+1]
        
        if prev_n > 0 and curr_n > 0 and next_n > 0:
            # 如果中间音比两边都高很多，或者都低很多
            if (curr_n > prev_n + 4 and curr_n > next_n + 4) or \
               (curr_n < prev_n - 4 and curr_n < next_n - 4):
                # 取平均值
                avg = int((prev_n + next_n) / 2)
                melody[i] = avg
    return melody

def op_shadow_echo(melody):
    """影子/回声"""
    for i in range(len(melody) - 1):
        if melody[i] > 0 and melody[i+1] == 0:
            if random.random() < 0.3: 
                melody[i+1] = melody[i] 
                return melody 
    return melody

def op_rhythm_clone(melody):
    """动机克隆"""
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    if len(melody) >= 3 * steps_per_bar:
        bar0 = melody[0:steps_per_bar]
        bar2_start = 2 * steps_per_bar
        for i in range(steps_per_bar):
            if bar0[i] > 0:
                if melody[bar2_start + i] == 0:
                    melody[bar2_start + i] = random.choice(list(config.SCALE_C_MAJOR)) + 60
            else:melody[bar2_start + i] = 0
    return melody

def op_retrograde_segment(melody):
    """局部逆行"""
    length = 4 
    if len(melody) <= length: return melody
    start = random.randint(0, len(melody) - length)
    segment = melody[start : start+length]
    melody[start : start+length] = segment[::-1]
    return melody

def op_inversion_segment(melody):
    """局部倒影"""
    length = 4
    if len(melody) <= length: return melody
    start = random.randint(0, len(melody) - length)
    segment = melody[start : start+length]
    if not segment: return melody
    pivot = segment[0]
    if pivot == 0: pivot = 72 
    for i in range(length):
        if melody[start+i] > 0:
            dist = melody[start+i] - pivot
            new_pitch = pivot - dist
            new_pitch = max(config.PITCH_MIN, min(config.PITCH_MAX, new_pitch))
            melody[start+i] = new_pitch
    return melody

def crossover(p1, p2):
    """单点交叉"""
    if len(p1) < 2: return p1, p2
    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:], p2[:point] + p1[point:]


class GAEngine:
    def __init__(self, target_gens=None, population_size=None, mutation_rate=None):
        self.target_gens = target_gens if target_gens else config.GENERATIONS
        self.pop_size = population_size if population_size else config.POPULATION_SIZE
        self.base_mutation_rate = mutation_rate if mutation_rate else config.MUTATION_RATE_BASE

    def mutate_dispatcher(self, melody, rate):
        if random.random() > rate: return melody
        new_melody = melody[:] 
        
        # 定义变异策略池及其权重
        strategies = [
            (op_micro_adjust,     0.30), 
            (op_transpose,        0.10), # 移调
            (op_smooth_contour,   0.10), # 去锯齿
            (op_shadow_echo,      0.15), 
            (op_rhythm_clone,     0.10), 
            (op_retrograde_segment, 0.05),
            (op_inversion_segment,  0.05),
            (utils.generate_random_melody, 0.15) # 重置
        ]
        
        r = random.random()
        cumulative = 0
        for func, weight in strategies:
            cumulative += weight
            if r < cumulative:
                if func == utils.generate_random_melody:
                    return func() 
                return func(new_melody)
        
        return new_melody

    def train(self, initial_seed=None, constraints_override=None):
        """执行遗传算法训练"""
        original_settings = {}
        if constraints_override:
            for k, v in constraints_override.items():
                if hasattr(config, k):
                    original_settings[k] = getattr(config, k)
                    setattr(config, k, v)
                    print(f"  [Config Override] Set {k} = {v}")

        try:
            # 2. 初始化种群
            if initial_seed:
                population = [self.mutate_dispatcher(initial_seed[:], 0.2) for _ in range(self.pop_size)]
                print(f"  [Init] Pop initialized from Seed.")
            else:
                population = [utils.generate_random_melody() for _ in range(self.pop_size)]
                print(f"  [Init] Pop initialized randomly (Random Walk).")

            stats = {'stag_count': 0, 'best_score': -9999, 'mut_rate': self.base_mutation_rate}

            print(f"Start Training: {self.target_gens} Gens")

            for gen in range(self.target_gens):
                valid_pop = [ind for ind in population if len(ind) > 0]
                if not valid_pop: valid_pop = [utils.generate_random_melody() for _ in range(self.pop_size)]
                
                scored_pop = [(get_fitness(ind), ind) for ind in valid_pop]
                scored_pop.sort(key=lambda x: x[0], reverse=True)
                
                current_best_score, best_melody = scored_pop[0]
                
                if current_best_score > stats['best_score'] + 0.1:
                    stats['stag_count'] = 0
                    stats['best_score'] = current_best_score
                    stats['mut_rate'] = self.base_mutation_rate 
                else:
                    stats['stag_count'] += 1
                    if stats['stag_count'] > 10: stats['mut_rate'] = min(0.8, self.base_mutation_rate * 2.0)
                    
                # 灾难机制
                if stats['stag_count'] > 50:
                    print(f"[灭绝] Gen {gen}: 重置种群。")
                    survivors = [p[1] for p in scored_pop[:5]] 
                    new_blood = [utils.generate_random_melody() for _ in range(self.pop_size - 5)]
                    population = survivors + new_blood
                    stats['stag_count'] = 0
                    continue 

                # 繁殖
                new_pop = []
                elite_count = config.ELITISM_COUNT
                new_pop.extend([p[1] for p in scored_pop[:elite_count]])
                
                while len(new_pop) < self.pop_size:
                    parent1 = max(random.sample(scored_pop, 5), key=lambda x:x[0])[1]
                    parent2 = max(random.sample(scored_pop, 5), key=lambda x:x[0])[1]
                    child1, child2 = crossover(parent1, parent2)
                    child1 = self.mutate_dispatcher(child1, stats['mut_rate'])
                    child2 = self.mutate_dispatcher(child2, stats['mut_rate'])
                    new_pop.extend([child1, child2])
                    
                population = new_pop[:self.pop_size]

                if gen % 20 == 0 or gen == self.target_gens - 1:
                    print(f"Gen {gen:03d} | Best: {current_best_score:.2f}")

            return scored_pop[0][1]
        
        finally:
            for k, v in original_settings.items():
                setattr(config, k, v)



def get_user_chord_progression():
    """获取输入的和弦走向"""
    print("\n请输入和弦走向 MIDI 根音 (以逗号分隔，默认: 48, 43, 45, 41)")
    print("参考: C3=48, D3=50, E3=52, F3=53, G3=55, A3=57, B3=59")
    user_input = input("Chords > ").strip()
    if not user_input:
        return None
    try:
        roots = [int(x.strip()) for x in user_input.split(',')]
        return roots
    except ValueError:
        print("输入格式错误，使用默认值。")
        return None

def train(**kwargs):
    engine = GAEngine(**kwargs)
    return engine.train()

if __name__ == "__main__":
    # 交互式运行
    user_chords = get_user_chord_progression()
    
    constraints = {}
    if user_chords:
        constraints['CHORD_ROOTS'] = user_chords
        # 还要调整时长，防止和弦数和旋律长度不匹配
        # 这里简单假设 config 足够长
        print(f"使用自定义和弦: {user_chords}")
    
    engine = GAEngine(target_gens=500) # 演示用500代
    final_melody = engine.train(constraints_override=constraints)
    utils.save_melody_to_midi(final_melody, "music.mid")