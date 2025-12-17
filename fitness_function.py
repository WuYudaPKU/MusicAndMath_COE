# MusicAndMath/fitness_function.py
import config

# 1. 静态常量
SCALE_C_MAJOR = {0, 2, 4, 5, 7, 9, 11}

# 律动模版
GROOVE_TEMPLATES = {
    # --- 基础节奏 (Basic) ---
    (1, 0, 1, 0, 1, 0, 1, 0): 10,  # 标准四分音符 (稳重)
    (1, 0, 0, 0, 1, 0, 0, 0): 5,   # 二分音符 (空灵)
    (1, 0, 1, 0, 1, 0, 0, 0): 10,  # 前紧后松
    (1, 0, 0, 0, 1, 0, 1, 0): 10,  # 前松后紧 (推进感)
    (1, 1, 1, 1, 1, 1, 1, 1): 4,   # 密集八分音符 (能量强，但易单调)

    # --- 经典流行/切分 (Pop & Syncopation) ---
    (1, 0, 0, 1, 0, 0, 1, 0): 15,  # [强烈推荐] Tresillo 节奏 (3+3+2)，Reggaeton/Pop 核心
    (1, 0, 0, 1, 0, 0, 0, 0): 15,  # Charleston 变体 (前半部分)
    (1, 0, 1, 0, 1, 0, 0, 1): 15,  # 你的模版：最后切分抢拍 (Anticipation)
    (1, 0, 0, 1, 1, 0, 1, 0): 15,  # 你的模版：中间切分

    # --- 摇滚/驱动 (Rock/Driving) ---
    (1, 0, 1, 1, 1, 0, 1, 0): 12,  # 带有驱动力的摇滚节奏
    (1, 0, 1, 1, 0, 1, 0, 0): 12,  # 经典切分驱动
    (1, 0, 1, 0, 1, 1, 1, 0): 12,  # 结尾推动

    # --- 放克/律动 (Funk/Groove) ---
    (1, 0, 1, 1, 0, 1, 1, 0): 18,  # Funky 切分
    (1, 1, 0, 1, 0, 1, 0, 0): 15,  # 16分音符感觉的错位 (假设速度较慢时)
    (1, 0, 0, 0, 1, 1, 0, 1): 15,  # 后半拍活跃

    (1, 0, 1, 1, 1, 1, 0, 0): 10,
    (1, 0, 1, 1, 0, 0, 1, 0): 10,
    (1, 0, 1, 1, 1, 1, 1, 0): 5,
    (1, 0, 1, 1, 1, 0, 0, 0): 10,
    (1, 1, 0, 1, 1, 0, 1, 0): 15,
}
def get_dynamic_chords():
    """
    根据 config.CHORD_ROOTS 动态构建每一小节的和弦组成音。
    自动构建 C 大调顺阶三和弦。
    """
    chords = []
    for root in config.CHORD_ROOTS:
        root_pc = root % 12
        # C大调顺阶构建逻辑
        # C(0), D(2), E(4), F(5), G(7), A(9), B(11)
        # 对应音阶索引: 0, 1, 2, 3, 4, 5, 6
        scale_indices = [0, 2, 4, 5, 7, 9, 11]
        
        if root_pc in scale_indices:
            idx = scale_indices.index(root_pc)
            # 取 1, 3, 5 度 (在音阶列表中的索引分别是 idx, idx+2, idx+4)
            # 注意循环取模
            note1 = scale_indices[idx]
            note2 = scale_indices[(idx + 2) % 7]
            note3 = scale_indices[(idx + 4) % 7]
            chords.append({note1, note2, note3})
        else:
            # 如果根音不在调内，默认给个大三和弦兜底
            chords.append({root_pc, (root_pc+4)%12, (root_pc+7)%12})
    return chords

# 2. 核心预处理 (保持不变)
def analyze_melody(melody):
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    events = [(i, n) for i, n in enumerate(melody) if n > 0]
    bars = [melody[i:i+steps_per_bar] for i in range(0, len(melody), steps_per_bar)]
    return events, bars, steps_per_bar

# 3. 旋律层 (微调：使用 dynamic chords)
def fit_melodic_flow(events):
    if len(events) < 2: return 0
    score = 0
    pitches = [e[1] for e in events]
    
    # 获取当前和弦列表
    current_chords = get_dynamic_chords()
    num_bars = len(current_chords)
    
    for i in range(len(pitches) - 1):
        curr_p = pitches[i]
        next_p = pitches[i+1]
        interval = abs(next_p - curr_p)
        if interval <= 2: score += 5       
        elif interval <= 4: score += 2     
        elif interval > 7: score -= 10      
        elif interval > 12: score -= 20    
        
        # 惯性检查 (保持不变)
        if i < len(pitches) - 2:
            next_next_p = pitches[i+2]
            d1 = next_p - curr_p
            d2 = next_next_p - next_p
            if abs(d1) > 5:
                if d1 * d2 < 0 or d2 == 0: score += 10
                else: score -= 5
            elif abs(d1) <= 4 and abs(d2) <= 4 and d1 * d2 > 0:
                score += 5

    # 张力解决
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    for i in range(len(events) - 1):
        curr_idx, curr_p = events[i]
        next_idx, next_p = events[i+1]
        
        curr_bar_idx = (curr_idx // steps_per_bar) % num_bars
        curr_chord = current_chords[curr_bar_idx]
        
        if (curr_p % 12) not in curr_chord:
            next_bar_idx = (next_idx // steps_per_bar) % num_bars
            next_chord = current_chords[next_bar_idx]
            if abs(next_p - curr_p) <= 2 and (next_p % 12) in next_chord:
                score += 30 
    return score

# 4. 节奏与和声层
def fit_harmonic_quality(events, steps_per_beat=2):
    score = 0
    steps_per_bar = config.BEATS_PER_BAR * steps_per_beat
    
    # 动态获取和弦
    current_chords = get_dynamic_chords()
    num_bars = len(current_chords)
    
    for idx, pitch in events:
        bar_idx = (idx // steps_per_bar) % num_bars
        chord = current_chords[bar_idx]
        pc = pitch % 12
        is_strong_beat = (idx % steps_per_beat == 0)
        
        if pc in chord:
            score += 10 if is_strong_beat else 5
        elif pc in SCALE_C_MAJOR:
            score -= 2 
        else:
            score -= 30 
    return score

# 5. 节奏律动 (保持不变)
def fit_rhythm_groove(bars):
    score = 0
    # 确保只使用强拍开始的模版（请确认 GROOVE_TEMPLATES 里没有以 0 开头的模版）
    
    for bar_segment in bars:
        rhythm = []
        for i, n in enumerate(bar_segment):
            is_onset = False
            # 逻辑：只要是音符(>0)，且跟前一个不同(或是第一拍)，就算起音
            if n > 0:
                if i == 0: is_onset = True
                elif n != bar_segment[i-1]: is_onset = True
            rhythm.append(1 if is_onset else 0)
        
        rhythm_tuple = tuple(rhythm)
        
        # --- 修改 1：严格匹配，删除原有的 shift 循环 ---
        if rhythm_tuple in GROOVE_TEMPLATES:
            score += GROOVE_TEMPLATES[rhythm_tuple]
        else:
            # 没对上模版，检查是否太稀疏
            onsets = sum(rhythm)
            if onsets > 6: score -= 5 
            if onsets <= 1: score -= 10

        # --- 修改 2：死刑判决 ---
        # 只要这一小节的第一拍是休止符，无论后面多好，直接重罚
        if rhythm[0] == 0:
            score -= 50  # 扣分力度要大，让它在进化中直接被淘汰
    return score

# 6. 结构层 (保持不变)
def fit_structure_coherence(events, bars):
    if not events: return -100
    score = 0
    last_idx, last_pitch = events[-1]
    if last_pitch % 12 == 0: score += 20     
    elif last_pitch % 12 in {7, 11}: score += 5 
    
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    mid_events = [e for e in events if steps_per_bar <= e[0] < 2*steps_per_bar]
    if mid_events:
        mid_pitch = mid_events[-1][1]
        if mid_pitch % 12 in {2, 7, 11}: score += 15 
        
    if len(bars) >= 3:
        def get_onset_pattern(segment):
            res = []
            for i, n in enumerate(segment):
                is_onset = (n > 0) and (i==0 or n != segment[i-1])
                res.append(1 if is_onset else 0)
            return res
        r0 = get_onset_pattern(bars[0])
        r2 = get_onset_pattern(bars[2])
        if r0 == r2: score += 15
        elif sum(1 for a,b in zip(r0,r2) if a==b) >= len(r0)*0.75: score += 10
    return score

def fit_beat_stability(melody):
    """
    新增：节奏稳定性控制
    1. 强拍必须有声
    2. 抑制反拍起音
    3. 鼓励适当延音
    """
    score = 0
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT # 通常为8
    
    # --- A. 密度与延音检测 ---
    changes = 0
    for i in range(1, len(melody)):
        # 只要当前格与前一格不同（换音或变休止），就算一次变化
        if melody[i] != melody[i-1]:
            changes += 1
    
    # 计算密度 (0.0 - 1.0)
    density = changes / len(melody)
    
    # 期望密度：不要太碎，也不要死水一潭
    if density > 0.5: 
        score -= 6 # 扣分：变化太频繁，缺乏延音
    elif density < 0.1:
        score -= 6  # 扣分：太长不动
    else:
        score += 7 # 奖励：适中的延音（density 0.1~0.5）

    # --- B. 强拍与反拍检查 ---
    for i, note in enumerate(melody):
        step_in_bar = i % steps_per_bar
        if step_in_bar == 0: # 只针对每小节第1拍（Downbeat）
            if note == 0:score -= 100 # 重罚：强拍是休止符
            else:
                # 检查是否是“起音”（Onset）：
                # 1. 如果是全曲第1个音 (i==0)，当然是起音
                # 2. 如果当前音与前一个音不同 (note != melody[i-1])，说明是新敲击的音
                # 3. 注意：如果前一个音是休止符(0)，当前是音符，那肯定也是起音，包含在!=逻辑里了
                is_onset = (i == 0) or (note != melody[i-1])
                
                if is_onset:score += 20  # 奖励：强拍有力地敲下去了
                else:score -= 20  # 惩罚：强拍是拖过来的延音，没有力度

        elif step_in_bar == 4:
            if note == 0:
                score -= 20 # 次强拍惩罚稍微轻一点
            # 次强拍通常允许延音，所以这里可以不强制要求起音

        # [反拍抑制]
        # 假设 STEPS_PER_BEAT=2，奇数位置(1, 3, 5...)是反拍
        if i % 2 != 0:
            # 检查是否是“起音点”
            # 起音定义：当前是音符，且与前一个状态不同
            is_onset = (note > 0) and (i == 0 or note != melody[i-1])
            
            if is_onset:
                score -= 15 # 扣分：反拍起音（听感不稳定）

    return score

# 7. 总控 (保持不变)
def get_fitness(melody):
    if sum(melody) == 0: return -9999
    events, bars, _ = analyze_melody(melody)
    if not events: return -999
    
    s_melody    = fit_melodic_flow(events)
    s_harmony   = fit_harmonic_quality(events)
    s_rhythm    = fit_rhythm_groove(bars)
    s_structure = fit_structure_coherence(events, bars)
    
    # 新增稳定性评分
    s_stability = fit_beat_stability(melody)
    
    # 调整权重：大幅提升 Rhythm 和 Stability 的比重
    total = (2.0 * s_melody) + \
            (3.0 * s_harmony) + \
            (4.0 * s_rhythm) + \
            (2.1 * s_stability) + \
            (2.0 * s_structure)
    return total