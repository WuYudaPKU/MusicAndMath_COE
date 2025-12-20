# MusicAndMath/fitness_function.py
import config
import torch
import torch.nn.functional as F
from model import MelodyTransformer
import os

_NN_EVALUATOR = None

def get_nn_score(melodies):
    global _NN_EVALUATOR
    if not config.USE_NN_FITNESS or not melodies:
        return [0] * len(melodies)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    if _NN_EVALUATOR is None:
        _NN_EVALUATOR = MelodyTransformer(config.VOCAB_SIZE).to(device)
        if os.path.exists(config.NN_MODEL_PATH):
            _NN_EVALUATOR.load_state_dict(torch.load(config.NN_MODEL_PATH, map_location=device))
        _NN_EVALUATOR.eval()

    batch_tensor = torch.tensor(melodies, dtype=torch.long).to(device)
    sz = batch_tensor.size(1)
    mask = torch.triu(torch.ones(sz, sz), diagonal=1).bool().to(device)

    with torch.no_grad():
        logits = _NN_EVALUATOR(batch_tensor, mask=mask) 
        shift_logits = logits[:, :-1, :].contiguous()
        shift_labels = batch_tensor[:, 1:].contiguous()
        loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), 
                              shift_labels.view(-1), reduction='none')
        individual_losses = loss.view(batch_tensor.size(0), -1).mean(dim=1)
        
    return (-individual_losses).cpu().tolist()

SCALE_C_MAJOR = {0, 2, 4, 5, 7, 9, 11}

GROOVE_TEMPLATES = {
    # --- 基础节奏 (Basic) ---
    (1, 0, 1, 0, 1, 0, 1, 0): 10,  # 标准四分音符 (稳重)
    (1, 0, 0, 0, 1, 0, 0, 0): 5,   # 二分音符 (空灵)
    (1, 0, 1, 0, 1, 0, 0, 0): 10,  # 前紧后松
    (1, 0, 0, 0, 1, 0, 1, 0): 10,  # 前松后紧 (推进感)
    (1, 1, 1, 1, 1, 1, 1, 1): 4,   # 密集八分音符 (能量强，但易单调)

    # --- 经典流行/切分 (Pop & Syncopation) ---
    (1, 0, 0, 1, 0, 0, 1, 0): 15,  # Tresillo 节奏 (3+3+2)，Reggaeton/Pop 核心
    (1, 0, 0, 1, 0, 0, 0, 0): 15,  # Charleston 变体 (前半部分)
    (1, 0, 1, 0, 1, 0, 0, 1): 15,  # 你的模版：最后切分抢拍 (Anticipation)
    (1, 0, 0, 1, 1, 0, 1, 0): 15,  # 你的模版：中间切分

    # --- 摇滚/驱动 (Rock/Driving) ---
    (1, 0, 1, 1, 1, 0, 1, 0): 12,  # 带有驱动力的摇滚节奏
    (1, 0, 1, 1, 0, 1, 0, 0): 12,  # 经典切分驱动
    (1, 0, 1, 0, 1, 1, 1, 0): 12,  # 结尾推动

    # --- 放克/律动 (Funk/Groove) ---
    (1, 0, 1, 1, 0, 1, 1, 0): 18,  # Funky 切分
    (1, 1, 0, 1, 0, 1, 0, 0): 15,  # 16分音符感觉的错位
    (1, 0, 0, 0, 1, 1, 0, 1): 15,  # 后半拍活跃

    (1, 0, 1, 1, 1, 1, 0, 0): 10,
    (1, 0, 1, 1, 0, 0, 1, 0): 10,
    (1, 0, 1, 1, 1, 1, 1, 0): 5,
    (1, 0, 1, 1, 1, 0, 0, 0): 10,
    (1, 1, 0, 1, 1, 0, 1, 0): 15,
}
def get_dynamic_chords():
    chords = []
    for root in config.CHORD_ROOTS:
        root_pc = root % 12
        scale_indices = [0, 2, 4, 5, 7, 9, 11]
        if root_pc in scale_indices:
            idx = scale_indices.index(root_pc)
            note1 = scale_indices[idx]
            note2 = scale_indices[(idx + 2) % 7]
            note3 = scale_indices[(idx + 4) % 7]
            chords.append({note1, note2, note3})
        else:
            chords.append({root_pc, (root_pc+4)%12, (root_pc+7)%12})
    return chords

def analyze_melody(melody):
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    events = [(i, n) for i, n in enumerate(melody) if n > 0]
    bars = [melody[i:i+steps_per_bar] for i in range(0, len(melody), steps_per_bar)]
    return events, bars, steps_per_bar

def fit_melodic_flow(events):
    if len(events) < 2: return 0
    score = 0
    pitches = [e[1] for e in events]
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
        if i < len(pitches) - 2:
            next_next_p = pitches[i+2]
            d1 = next_p - curr_p
            d2 = next_next_p - next_p
            if abs(d1) > 5:
                if d1 * d2 < 0 or d2 == 0: score += 10
                else: score -= 5
            elif abs(d1) <= 4 and abs(d2) <= 4 and d1 * d2 > 0:
                score += 5
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

def fit_harmonic_quality(events, steps_per_beat=2):
    score = 0
    steps_per_bar = config.BEATS_PER_BAR * steps_per_beat
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

def fit_rhythm_groove(bars):
    score = 0
    for bar_segment in bars:
        rhythm = []
        for i, n in enumerate(bar_segment):
            is_onset = False
            if n > 0:
                if i == 0: is_onset = True
                elif n != bar_segment[i-1]: is_onset = True
            rhythm.append(1 if is_onset else 0) 
        rhythm_tuple = tuple(rhythm) 
        if rhythm_tuple in GROOVE_TEMPLATES:
            score += GROOVE_TEMPLATES[rhythm_tuple]
        else:
            onsets = sum(rhythm)
            if onsets > 6: score -= 5 
            if onsets <= 1: score -= 10
        if rhythm[0] == 0:
            score -= 50
    return score

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
    score = 0
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT 
    changes = 0
    for i in range(1, len(melody)):
        if melody[i] != melody[i-1]:
            changes += 1
    density = changes / len(melody)
    if density > 0.5: 
        score -= 6
    elif density < 0.1:
        score -= 6
    else:
        score += 7
    for i, note in enumerate(melody):
        step_in_bar = i % steps_per_bar
        if step_in_bar == 0:
            if note == 0:score -= 100
            else:
                is_onset = (i == 0) or (note != melody[i-1])
                if is_onset:score += 20
                else:score -= 20
        elif step_in_bar == 4:
            if note == 0:
                score -= 20
        if i % 2 != 0:
            is_onset = (note > 0) and (i == 0 or note != melody[i-1])
            if is_onset:
                score -= 15

    return score

def get_fitness(melody,use_nn=False):
    if sum(melody) == 0: return -9999
    events, bars, _ = analyze_melody(melody)
    if not events: return -999
    s_melody    = fit_melodic_flow(events)
    s_harmony   = fit_harmonic_quality(events)
    s_rhythm    = fit_rhythm_groove(bars)
    s_structure = fit_structure_coherence(events, bars)
    s_stability = fit_beat_stability(melody)
    s_transformer = get_nn_score(melody)
    if use_nn:
        total=s_transformer
    else:
        total = (2.0 * s_melody) + \
            (3.0 * s_harmony) + \
            (4.0 * s_rhythm) + \
            (2.1 * s_stability) + \
            (2.0 * s_structure)
    return total