# main.py
import random
import config
import utils
from fitness_function import get_fitness 

# ==========================================
# 1. 乐理变异算子 (Musical Mutators)
# 让变异具有音乐性，而非单纯的随机数
# ==========================================

def op_micro_adjust(melody):
    """微调：上下移动 1-2 个半音，保持旋律形状"""
    idx = random.randint(0, len(melody)-1)
    if melody[idx] > 0:
        shift = random.choice([-2, -1, 1, 2])
        new_val = melody[idx] + shift
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
    """局部逆行：将一小段旋律倒着放 (巴赫常用技巧)"""
    length = 4 # 倒转 4 个步长（半个小节）
    start = random.randint(0, len(melody) - length)
    segment = melody[start : start+length]
    melody[start : start+length] = segment[::-1]
    return melody

def op_inversion_segment(melody):
    """局部倒影：以第一个音为轴，进行镜像翻转"""
    length = 4
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

# ==========================================
# 2. 遗传核心 (Engine)
# ==========================================

def mutate_dispatcher(melody, rate):
    """
    变异调度器：根据概率轮盘赌选择一种变异策略
    """
    if random.random() > rate: return melody
    
    new_melody = melody[:] # Copy
    
    # 定义变异策略池及其权重
    strategies = [
        (op_micro_adjust,     0.50), # 50% 概率只是微调 (最安全)
        (op_shadow_echo,      0.20), # 20% 增加律动
        (op_rhythm_clone,     0.10), # 10% 强化结构
        (op_retrograde_segment, 0.05), # 5%  整活：逆行
        (op_inversion_segment,  0.05), # 5%  整活：倒影
        (utils.generate_random_melody, 0.10) # 10% 彻底重置 (引入鲶鱼)
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

def crossover(p1, p2):
    """单点交叉：保持乐句完整性，比均匀交叉更好"""
    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:], p2[:point] + p1[point:]

# ==========================================
# 3. 训练主循环 (Clean Version)
# ==========================================

def train():
    TOTAL_GENS = 500
    POP_SIZE = config.POPULATION_SIZE
    
    # 初始化
    population = [utils.generate_random_melody() for _ in range(POP_SIZE)]
    
    # 状态追踪
    stats = {
        'stag_count': 0,
        'best_score': -9999,
        'mut_rate': config.MUTATION_RATE_BASE
    }
    
    print(f"Start Training: {TOTAL_GENS} Gens | Pop {POP_SIZE}")

    for gen in range(TOTAL_GENS):
        # 1. 评估与排序
        scored_pop = [(get_fitness(ind), ind) for ind in population]
        scored_pop.sort(key=lambda x: x[0], reverse=True)
        
        current_best_score, best_melody = scored_pop[0]
        
        # 2. 停滞检测与自适应 (封装逻辑)
        if current_best_score > stats['best_score'] + 0.1:
            stats['stag_count'] = 0
            stats['best_score'] = current_best_score
            stats['mut_rate'] = config.MUTATION_RATE_BASE # 进展顺利，保持稳定
        else:
            stats['stag_count'] += 1
            # 动态调整变异率：越停滞，越焦虑
            if stats['stag_count'] > 10: stats['mut_rate'] = 0.2
            if stats['stag_count'] > 30: stats['mut_rate'] = 0.5
            
        # 3. 灾难机制 (Cataclysm)
        if stats['stag_count'] > 50:
            print(f"  >>> [灭绝] Gen {gen}: 陷入局部最优，重置种群...")
            # 只留前3个精英，其余全部随机重置
            survivors = [p[1] for p in scored_pop[:3]]
            new_blood = [utils.generate_random_melody() for _ in range(POP_SIZE - 3)]
            population = survivors + new_blood
            stats['stag_count'] = 0
            continue # 跳过本轮

        # 4. 繁殖下一代
        new_pop = []
        
        # [A] 精英保留 (Top 5%)
        elite_count = int(POP_SIZE * 0.05)
        new_pop.extend([p[1] for p in scored_pop[:elite_count]])
        
        # [B] 锦标赛选择与交叉
        while len(new_pop) < POP_SIZE:
            # 选取父母 (Tournament Size = 5)
            parent1 = max(random.sample(scored_pop, 5), key=lambda x:x[0])[1]
            parent2 = max(random.sample(scored_pop, 5), key=lambda x:x[0])[1]
            
            # 交叉
            child1, child2 = crossover(parent1, parent2)
            
            # 变异 (使用调度器)
            child1 = mutate_dispatcher(child1, stats['mut_rate'])
            child2 = mutate_dispatcher(child2, stats['mut_rate'])
            
            new_pop.extend([child1, child2])
            
        # 截断以防溢出 (如果是奇数)
        population = new_pop[:POP_SIZE]

        # 日志
        if gen % 20 == 0:
            print(f"Gen {gen:03d} | Best: {current_best_score:.2f} | Stag: {stats['stag_count']} | Mut: {stats['mut_rate']:.2f}")

    return scored_pop[0][1]

if __name__ == "__main__":
    final_melody = train()
    utils.save_melody_to_midi(final_melody, "final_gen_music.mid")