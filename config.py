# config.py

NUM_BARS = 4            # 【生成长度】旋律包含的小节数。4小节是典型的乐句长度。
BEATS_PER_BAR = 4       # 【拍号】每小节几拍。4代表 4/4 拍，这是最常见的流行音乐拍号。
STEPS_PER_BEAT = 2      # 【时间精度】每拍被切分成几份。2 代表最小单位是八分音符。

TOTAL_STEPS = NUM_BARS * BEATS_PER_BAR * STEPS_PER_BEAT 


# 【音域范围】MIDI 编号。
# 60=中央C (C4)。50(D3) 到 84(C6) 跨越了约 3 个八度。
PITCH_MIN = 60          
PITCH_MAX = 84          

# 【稀疏度】生成休止符（0）的概率。
# 0.3 表示约 30% 的时间是静音的。
# 调大该值：旋律更空灵、呼吸感更强；调小该值：旋律更紧凑、密集。
REST_PROB = 0.3


# 【种群规模】每一代包含多少个独立的旋律。
POPULATION_SIZE = 1000  

# 【迭代次数】进化的总轮数。
GENERATIONS = 200       

# 【基础变异率】基因突变的概率。
# 0.05 (5%) 代表在通过交叉产生后代后，每个音符有 5% 的概率随机变成其他音。
MUTATION_RATE_BASE = 0.05 

# 【精英策略】每代直接晋级下一代的“最强王者”数量。
# 代表每一代评分最高的个体不经过交叉变异，直接复制到下一代。
ELITISM_COUNT = 200     

# 【和弦走向】定义了背景音乐的根音序列。
# 48(C3), 43(G2), 45(A2), 41(F2) 对应经典的流行走向：C大调 I - V - vi - IV
CHORD_ROOTS = [48, 43, 45, 41] 

# 【和弦节奏】每个和弦持续的拍数。
# 4 代表每个和弦占满 1 个小节（全音符长度）。
CHORD_DURATION = 4 

# 【C大调音阶集合】用于变异算子和适应度计算
# Pitch Classes: 0=C, 2=D, 4=E, 5=F, 7=G, 9=A, 11=B
SCALE_C_MAJOR = {0, 2, 4, 5, 7, 9, 11}

USE_NN_FITNESS = True
NN_MODEL_PATH = "lmd_eval.pth"
VOCAB_SIZE = 130