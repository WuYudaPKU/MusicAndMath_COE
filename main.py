# main.py
import random
import config
import utils
from fitness_function import get_fitness 

# ==========================================
# 1. 乐理变异算子 (Musical Mutators)
# 这些函数保持独立，方便被调度器调用
# ==========================================

def op_micro_adjust(melody):
    """微调：上下移动 1-2 个半音，保持旋律形状"""
    if len(melody) == 0: return melody
    idx = random.randint(0, len(melody)-1)
    if melody[idx] > 0:
        shift = random.choice([-2, -1, 1, 2])
        new_val = melody[idx] + shift
        # 确保在有效音域内
        if config.PITCH_MIN <= new_val <= config.PITCH_MAX:
            melody[idx] = new_val
    return melody

def op_shadow_echo(melody):
    """
    影子/回声：将前一个音的“影子”投射到下一个空拍上。
    效果：制造切分音和延绵感。
    """
    for i in range(len(melody) - 1):
        # 如果当前有音，且下一个位置是空拍
        if melody[i] > 0 and melody[i+1] == 0:
            if random.random() < 0.3: # 30% 概率触发回声
                melody[i+1] = melody[i] # 重复该音
                return melody # 一次只变一处，保持稳定
    return melody

def op_rhythm_clone(melody):
    """动机克隆：将 Bar 0 的节奏强行复制到 Bar 2"""
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    if len(melody) >= 3 * steps_per_bar:
        bar0 = melody[0:steps_per_bar]
        bar2_start = 2 * steps_per_bar
        for i in range(steps_per_bar):
            # 只复制节奏(0/1关系)，保留 Bar 2 原有的音高(如果有的话)，或者赋予新音高
            if bar0[i] > 0:
                # 如果 Bar 2 该位置本来是空的，填一个随机调内音
                if melody[bar2_start + i] == 0:
                    melody[bar2_start + i] = random.choice(list(config.SCALE_C_MAJOR)) + 60
            else:
                melody[bar2_start + i] = 0
    return melody

def op_retrograde_segment(melody):
    """局部逆行：将一小段旋律倒着放"""
    length = 4 # 倒转 4 个步长（半个小节）
    if len(melody) <= length: return melody
    
    start = random.randint(0, len(melody) - length)
    segment = melody[start : start+length]
    melody[start : start+length] = segment[::-1]
    return melody

def op_inversion_segment(melody):
    """局部倒影：以第一个音为轴，进行镜像翻转"""
    length = 4
    if len(melody) <= length: return melody
    
    start = random.randint(0, len(melody) - length)
    segment = melody[start : start+length]
    if not segment: return melody
    
    pivot = segment[0]
    if pivot == 0: pivot = 72 # 默认轴
    
    for i in range(length):
        if melody[start+i] > 0:
            # 公式: 新音 = 轴 - (原音 - 轴)
            dist = melody[start+i] - pivot
            new_pitch = pivot - dist
            # 修正音域
            new_pitch = max(config.PITCH_MIN, min(config.PITCH_MAX, new_pitch))
            melody[start+i] = new_pitch
    return melody

def crossover(p1, p2):
    """单点交叉：保持乐句完整性，比均匀交叉更好"""
    if len(p1) < 2: return p1, p2
    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:], p2[:point] + p1[point:]


# ==========================================
# 2. 遗传核心 (GAEngine)
# 封装了训练逻辑，支持配置隔离
# ==========================================

class GAEngine:
    def __init__(self, target_gens=None, population_size=None, mutation_rate=None):
        """
        初始化引擎参数
        :param target_gens: 目标代数，None 则使用 config.GENERATIONS
        :param population_size: 种群大小，None 则使用 config.POPULATION_SIZE
        :param mutation_rate: 基础变异率，None 则使用 config.MUTATION_RATE_BASE
        """
        self.target_gens = target_gens if target_gens else config.GENERATIONS
        self.pop_size = population_size if population_size else config.POPULATION_SIZE
        self.base_mutation_rate = mutation_rate if mutation_rate else config.MUTATION_RATE_BASE

    def mutate_dispatcher(self, melody, rate):
        """
        变异调度器：根据概率轮盘赌选择一种变异策略
        """
        if random.random() > rate: return melody
        
        new_melody = melody[:] # Copy
        
        # 定义变异策略池及其权重
        strategies = [
            (op_micro_adjust,     0.40), # 50% 微调，稳定
            (op_shadow_echo,      0.20), # 20% 增加律动
            (op_rhythm_clone,     0.10), # 10% 强化结构
            (op_retrograde_segment, 0.1), # 5%  整活：逆行
            (op_inversion_segment,  0.1), # 5%  整活：倒影
            (utils.generate_random_melody, 0.10) # 10% 彻底重置
        ]
        
        # 轮盘赌选择
        r = random.random()
        cumulative = 0
        for func, weight in strategies:
            cumulative += weight
            if r < cumulative:
                # 如果是重置函数，不需要传参
                if func == utils.generate_random_melody:
                    return func() 
                return func(new_melody)
        
        return new_melody

    def train(self, initial_seed=None, constraints_override=None):
        """
        执行遗传算法训练
        :param initial_seed: (List) 种子旋律。如果提供，初始种群将基于此变异而来（用于变奏）。
        :param constraints_override: (Dict) 临时覆盖 config 中的常量，例如 {'PITCH_MIN': 72}。
        :return: 训练出的最佳旋律
        """
        
        # --- 1. 上下文配置管理 (Context Override) ---
        # 临时修改全局 config，确保训练结束后恢复，防止污染其他乐章
        original_settings = {}
        if constraints_override:
            for k, v in constraints_override.items():
                if hasattr(config, k):
                    original_settings[k] = getattr(config, k)
                    setattr(config, k, v)
                    print(f"  [Config Override] Set {k} = {v}")

        # 使用 try-finally 确保配置一定会被还原
        try:
            # --- 2. 初始化种群 ---
            if initial_seed:
                # 变奏模式：基于种子进行轻微扰动
                # 使用较高的初始变异率(0.2)来保证种群多样性，否则全是克隆体
                population = [self.mutate_dispatcher(initial_seed[:], 0.2) for _ in range(self.pop_size)]
                print(f"  [Init] Population initialized from Seed (Length: {len(initial_seed)})")
            else:
                # 创作模式：完全随机
                population = [utils.generate_random_melody() for _ in range(self.pop_size)]
                print(f"  [Init] Population initialized randomly.")

            # 状态追踪
            stats = {
                'stag_count': 0,
                'best_score': -9999,
                'mut_rate': self.base_mutation_rate
            }

            print(f"Start Training: {self.target_gens} Gens | Pop {self.pop_size} | Base MutRate {self.base_mutation_rate}")

            for gen in range(self.target_gens):
                # [A] 评估与排序
                # 过滤无效旋律（避免空列表报错）
                valid_pop = [ind for ind in population if len(ind) > 0]
                if not valid_pop: valid_pop = [utils.generate_random_melody() for _ in range(self.pop_size)]
                
                scored_pop = [(get_fitness(ind), ind) for ind in valid_pop]
                scored_pop.sort(key=lambda x: x[0], reverse=True)
                
                current_best_score, best_melody = scored_pop[0]
                
                # [B] 停滞检测与自适应
                if current_best_score > stats['best_score'] + 0.1:
                    stats['stag_count'] = 0
                    stats['best_score'] = current_best_score
                    # 进展顺利，恢复到基础变异率
                    stats['mut_rate'] = self.base_mutation_rate 
                else:
                    stats['stag_count'] += 1
                    # 动态调整变异率：越停滞，越焦虑
                    if stats['stag_count'] > 10: stats['mut_rate'] = min(0.8, self.base_mutation_rate * 2.0)
                    if stats['stag_count'] > 30: stats['mut_rate'] = min(0.9, self.base_mutation_rate * 3.0)
                    
                # [C] 灾难机制 (Cataclysm)
                # 如果停滞太久，保留极少数精英，其余重置
                if stats['stag_count'] > 50:
                    print(f"  >>> [灭绝] Gen {gen}: 陷入局部最优 (Score: {current_best_score:.2f})，重置种群...")
                    survivors = [p[1] for p in scored_pop[:5]] # 只留5个
                    new_blood = [utils.generate_random_melody() for _ in range(self.pop_size - 5)]
                    population = survivors + new_blood
                    stats['stag_count'] = 0
                    stats['mut_rate'] = self.base_mutation_rate
                    continue 

                # [D] 繁殖下一代
                new_pop = []
                
                # 精英保留 (Elitism)
                elite_count = config.ELITISM_COUNT
                new_pop.extend([p[1] for p in scored_pop[:elite_count]])
                
                # 交叉与变异
                while len(new_pop) < self.pop_size:
                    # 锦标赛选择 (Tournament Selection)
                    # 从随机抽取的样本中选最好的，避免总是选全局最好的导致早熟
                    parent1 = max(random.sample(scored_pop, 5), key=lambda x:x[0])[1]
                    parent2 = max(random.sample(scored_pop, 5), key=lambda x:x[0])[1]
                    
                    # 交叉
                    child1, child2 = crossover(parent1, parent2)
                    
                    # 变异 (使用成员方法 dispatcher)
                    child1 = self.mutate_dispatcher(child1, stats['mut_rate'])
                    child2 = self.mutate_dispatcher(child2, stats['mut_rate'])
                    
                    new_pop.extend([child1, child2])
                    
                # 截断以防溢出
                population = new_pop[:self.pop_size]

                # 日志
                if gen % 20 == 0 or gen == self.target_gens - 1:
                    print(f"Gen {gen:03d} | Best: {current_best_score:.2f} | Stag: {stats['stag_count']} | Mut: {stats['mut_rate']:.2f}")

            return scored_pop[0][1]
        
        finally:
            # --- 3. 恢复配置 ---
            # 无论训练是否成功，都必须将 config 恢复原样
            for k, v in original_settings.items():
                setattr(config, k, v)
                # print(f"  [Config Restored] {k} -> {v}")

# ==========================================
# 3. 兼容旧代码的入口
# ==========================================

def train(**kwargs):
    """
    为了兼容可能直接调用 main.train() 的旧代码，
    这里提供一个简单的包装函数。
    """
    engine = GAEngine(**kwargs)
    return engine.train()

if __name__ == "__main__":
    # 单次运行测试
    final_melody = train()
    utils.save_melody_to_midi(final_melody, "music.mid")