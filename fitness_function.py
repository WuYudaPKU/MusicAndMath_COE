# fitness_function.py
import config


# 1. 静态常量 (CONSTANTS)
SCALE_C_MAJOR = {0, 2, 4, 5, 7, 9, 11}
CHORDS = [
    {0, 4, 7},      # Bar 0: C
    {7, 11, 2},     # Bar 1: G
    {9, 0, 4},      # Bar 2: Am
    {5, 9, 0}       # Bar 3: F
]

# 律动模版
GROOVE_TEMPLATES = {
    # --- 基础稳重型 (Base) ---
    # [标准8分音符] 适合作为背景铺垫
    (1, 0, 1, 0, 1, 0, 1, 0): 10,   
    # [四分音符] 稳健的步伐 (1, 3拍)
    (1, 0, 0, 0, 1, 0, 0, 0): 10,   

    # --- 流行与摇滚 (Pop/Rock) ---
    # [向前推动] 强调第4拍的反拍 (Push)，制造期待感
    (1, 0, 1, 0, 1, 0, 0, 1): 10, 
    # [切分摇滚]
    (1, 0, 0, 1, 0, 1, 0, 0): 10,

    # 拉丁与舞曲 (Latin/Dance)
    # [Tresillo] (3-3-2) 雷鬼、Reggaeton、Hiphop
    # 这种节奏打破了4/4拍的对称性，极具动感
    (1, 0, 0, 1, 0, 0, 1, 0): 10,  
    
    # [Habanera / Tango] 哈巴涅拉，卡门的节奏
    # 在 Tresillo 的基础上多了一个切分音
    (1, 0, 0, 1, 1, 0, 1, 0): 10,  

    # [Cinquillo] (2-1-2-1-2) 古巴音乐核心
    # 非常紧凑，适合高潮部分
    (1, 0, 1, 1, 0, 1, 1, 0): 10,  

    # --- 爵士与摇摆 (Jazz/Swing Feel)
    # [Charleston] 查尔斯顿节奏
    # 20年代摇摆乐经典
    (1, 0, 0, 1, 0, 0, 0, 0): 10,
    
    # [Syncopated Jazz] 连续的反拍切分
    (0, 1, 0, 1, 0, 1, 0, 1): 10,

    # 史诗与叙事 (Epic/Cinematic)
    # 适合静谧的开头
    (1, 0, 1, 0, 0, 0, 0, 0): 10,
    
    # [Gallop] 骑马节奏 (Iron Maiden 风格)
    (1, 1, 0, 1, 1, 0, 1, 0): 10,
}

# 2. 核心预处理
def analyze_melody(melody):
    """
    将原始旋律数组解构为两个独立的视图：
    1. events: 纯音符序列 [(index, pitch), ...] -> 用于评估旋律连贯性
    2. bars:   小节切片 -> 用于评估节奏律动
    """
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    
    # 视图1：音符事件链 (Melody Chain)
    # 过滤掉所有的 0，只保留 (时间点, 音高)
    # 这样，events[i] 的下一个音永远是 events[i+1]，无论中间隔了多少延音
    events = [(i, n) for i, n in enumerate(melody) if n > 0]
    
    # 视图2：小节切片 (Rhythm Grid)
    bars = [melody[i:i+steps_per_bar] for i in range(0, len(melody), steps_per_bar)]
    
    return events, bars, steps_per_bar


# 3. 旋律层 (只看 events)
def fit_melodic_flow(events):
    """
    评估旋律的横向连贯性 (Interval, Gap Fill, Inertia, Resolution)
    完全忽略延音的影响。
    """
    if len(events) < 2: return 0
    score = 0
    
    # 提取纯音高列表用于计算
    pitches = [e[1] for e in events]
    
    # 使用 zip 遍历：(当前音, 下个音)
    # 这里的 next_pitch 绝对是下一个发声的音，哪怕隔了3拍
    for i in range(len(pitches) - 1):
        curr_p = pitches[i]
        next_p = pitches[i+1]
        
        # 1. 音程 (Interval)
        interval = abs(next_p - curr_p)
        if interval <= 2: score += 5       # 级进
        elif interval <= 4: score += 2     # 小跳
        elif interval > 7: score -= 10      # 大跳
        elif interval > 12: score -= 20    # 只有人声不能唱的跨度才重罚
        
        # 2. 惯性与大跳补偿 (Gap Fill & Inertia)
        # 需要看三个音
        if i < len(pitches) - 2:
            next_next_p = pitches[i+2]
            d1 = next_p - curr_p
            d2 = next_next_p - next_p
            
            # 大跳(>5)后必须反向
            if abs(d1) > 5:
                if d1 * d2 < 0 or d2 == 0: score += 10
                else: score -= 5
            # 小跳同向奖励
            elif abs(d1) <= 4 and abs(d2) <= 4 and d1 * d2 > 0:
                score += 5

    # 3. 张力解决 (Tension & Resolution)
    # events 列表里，next_p 就是下一个真实的音
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    
    for i in range(len(events) - 1):
        curr_idx, curr_p = events[i]
        next_idx, next_p = events[i+1] # 拿到下一个真实音及其位置
        
        # 计算当前时刻的和弦
        curr_chord_idx = (curr_idx // steps_per_bar) % 4
        curr_chord = CHORDS[curr_chord_idx]
        
        # 如果当前是离调音 (非和弦音)
        if (curr_p % 12) not in curr_chord:
            # 检查是否解决到了下一个音
            next_chord_idx = (next_idx // steps_per_bar) % 4 # 注意：和弦要查下一个音发生时的和弦
            next_chord = CHORDS[next_chord_idx]
            
            # 解决条件：级进移动(<=2) 且 进入和弦内
            if abs(next_p - curr_p) <= 2 and (next_p % 12) in next_chord:
                score += 30 # 巨大的奖励，鼓励这种人性化的写法

    return score


# 4. 节奏与和声层 (看 events + Grid)
def fit_harmonic_quality(events, steps_per_beat=2):
    """
    评估纵向和声。
    只评估 Onset (起奏点)，延音不扣分也不加分。
    """
    score = 0
    steps_per_bar = config.BEATS_PER_BAR * steps_per_beat
    
    for idx, pitch in events:
        # 确定当时和弦
        bar_idx = (idx // steps_per_bar) % 4
        chord = CHORDS[bar_idx]
        pc = pitch % 12
        
        # 强拍定义
        is_strong_beat = (idx % steps_per_beat == 0)
        
        if pc in chord:
            score += 10 if is_strong_beat else 5
        elif pc in SCALE_C_MAJOR:
            # 宽容处理：只要在调内，虽然不是和弦音，稍微扣一点点即可
            # 因为如果是离调解决，fit_melodic_flow 会把分加回来的
            score -= 2 
        else:
            score -= 30 # 调外音还是得罚
            
    return score

def fit_rhythm_groove(bars):
    """
    增强版节奏评分：支持模版匹配、循环移位变体检测。
    """
    score = 0
    # 将模版转换为集合，方便快速查找
    # 我们只存 key (pattern)，value (score) 在查的时候再取
    template_keys = set(GROOVE_TEMPLATES.keys())
    
    for bar_segment in bars:
        # 1. 提取当前小节的节奏型
        rhythm = []
        for i, n in enumerate(bar_segment):
            is_onset = False
            if n > 0:
                if i == 0: is_onset = True
                elif n != bar_segment[i-1]: is_onset = True
            rhythm.append(1 if is_onset else 0)
        
        rhythm_tuple = tuple(rhythm)
        
        # --- 评分逻辑 ---
        
        # A. 完美匹配 (Perfect Match)
        if rhythm_tuple in GROOVE_TEMPLATES:
            score += GROOVE_TEMPLATES[rhythm_tuple]
            
        else:
            # B. 变体匹配 (Shifted Match)
            # 检查是否是某个名模版的“移位版本”
            # 例如：Tresillo 晚了一拍开始，依然很有律动感
            found_shift = False
            shifted = list(rhythm_tuple)
            
            # 尝试左移/右移 1-2 位
            for _ in range(len(shifted)):
                # 循环移位: [1, 0, 1] -> [0, 1, 1]
                shifted = shifted[-1:] + shifted[:-1] 
                shifted_tuple = tuple(shifted)
                
                if shifted_tuple in GROOVE_TEMPLATES:
                    # 这是一个“移位”的经典节奏
                    # 给分，但比原版稍微低一点
                    base_score = GROOVE_TEMPLATES[shifted_tuple]
                    score += base_score * 0.6 
                    found_shift = True
                    break
            
            if not found_shift:
                # C. 兜底惩罚
                # 如果既不是模版，也不是模版的变体，可能是杂乱的随机节奏
                # 只有当节奏点太碎时才惩罚
                onsets = sum(rhythm)
                if onsets > 5: score -= 5 # 太乱
                if onsets <= 1: score -= 5 # 太空

    return score


# 5. 结构层 (Macro)
def fit_structure_coherence(events, bars):
    """结构完整性"""
    if not events: return -100
    score = 0
    
    # 1. 终止式 (只看最后一个 Event)
    last_idx, last_pitch = events[-1]
    if last_pitch % 12 == 0: score += 20     # 回主音
    elif last_pitch % 12 in {7, 11}: score += 5 # 属音半终止
    
    # 2. 问答结构 (Bar 2 结束音)
    # 找到第2小节内的最后一个 Event
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    mid_events = [e for e in events if steps_per_bar <= e[0] < 2*steps_per_bar]
    if mid_events:
        mid_pitch = mid_events[-1][1]
        if mid_pitch % 12 in {2, 7, 11}: score += 15 # 悬念
        
    # 3. 动机重复 (Rhythm Motif)
    # 对比 Bar 0 和 Bar 2 的 Onset 模式
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


# 6. 总控
def get_fitness(melody):
    if sum(melody) == 0: return -9999
    
    # 1. 预处理 (一次性完成)
    events, bars, _ = analyze_melody(melody)
    if not events: return -999
    
    # 2. 计算各层分数
    # 现在的 events 已经跳过了所有的延音(0)
    # 所以 Melodic Flow 不会因为节奏稀疏而受到影响
    s_melody    = fit_melodic_flow(events)
    s_harmony   = fit_harmonic_quality(events)
    s_rhythm    = fit_rhythm_groove(bars)
    s_structure = fit_structure_coherence(events, bars)
    
    # 3. 归一化/平衡
    # 如果音符很少，sum求和的分数会天然偏低。
    # 我们不仅要看总分，还要看“平均质量”。
    # 但为了简单起见，我们给 s_melody 一个基于音符数量的补偿，或者调整权重。
    
    # 这里采用“加权求和”，权重根据经验微调
    total = (3.0 * s_melody) + \
            (3.0 * s_harmony) + \
            (8.0 * s_rhythm) + \
            (3.0 * s_structure)
            
    return total