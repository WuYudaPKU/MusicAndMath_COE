# MusicAndMath/utils.py
import random
from midiutil import MIDIFile
import config

def get_scale_notes(min_p, max_p):
    """获取指定范围内的所有 C 大调调内音"""
    return [p for p in range(min_p, max_p + 1) if (p % 12) in config.SCALE_C_MAJOR]

def generate_random_melody(length=config.TOTAL_STEPS):
    """
    根据配置生成随机基因 (优化版：随机游走 + 调内限制)
    """
    melody = []
    
    # 1. 准备调内音阶列表
    scale_notes = get_scale_notes(config.PITCH_MIN, config.PITCH_MAX)
    if not scale_notes:
        scale_notes = [60, 62, 64, 65, 67, 69, 71]

    # 2. 确定起点
    start_candidates = [n for n in scale_notes if 60 <= n <= 72]
    if not start_candidates: start_candidates = scale_notes
    current_pitch = random.choice(start_candidates)
    
    for i in range(length):
        # --- 修改点：强制第一拍发声 ---
        # 如果是第 0 个音（全曲第一拍），强制不休止
        if i % 8 == 0:  # 强制每一小节的第一拍发声
            should_rest = False
        else:
            should_rest = random.random() < config.REST_PROB

        if should_rest:
            melody.append(0)
        else:
            # ... (保持原有的随机游走逻辑不变) ...
            try:
                curr_idx = scale_notes.index(current_pitch)
            except ValueError:
                curr_idx = len(scale_notes) // 2

            step = random.choice([-2, -1, -1, 0, 0, 1, 1, 2]) 
            next_idx = max(0, min(len(scale_notes) - 1, curr_idx + step))
            
            if random.random() < 0.05:
                step = random.choice([-4, -3, 3, 4, 5])
                next_idx = max(0, min(len(scale_notes) - 1, curr_idx + step))
            
            current_pitch = scale_notes[next_idx]
            melody.append(current_pitch)
            
    return melody

def save_melody_to_midi(melody, filename="output.mid", tempo=80):
    """
    保存 MIDI 文件 (包含连音处理 & 和弦伴奏)
    """
    track = 0
    channel_melody = 0  # 旋律通道
    channel_chord = 1   # 和弦伴奏通道
    
    time = 0
    volume = 100
    
    step_duration = 1.0 / config.STEPS_PER_BEAT 
    
    MyMIDI = MIDIFile(1) 
    MyMIDI.addTempo(track, time, tempo)
    
    # --- 1. 旋律写入 ---
    if len(melody) > 0:
        current_pitch = melody[0]
        current_length = 1
        current_start = 0
    
    for i in range(1, len(melody)):
        note = melody[i]
        if note == current_pitch and note != 0:
            # 相同音高时，根据概率判断是否拆分（30%概率拆分，70%概率合并）
            if random.random() < 0.3:  # 增加拆分概率
                # 强制拆分：写入当前累积的音符
                MyMIDI.addNote(
                    track, channel_melody, current_pitch,
                    current_start * step_duration,
                    current_length * step_duration, volume
                )
                # 重置计数器，从当前位置开始新的音符
                current_start = i
                current_length = 1
            else:
                # 不拆分：继续累积长度
                current_length += 1
        else:
            if current_pitch != 0:
                MyMIDI.addNote(track, channel_melody, current_pitch, 
                               current_start * step_duration, 
                               current_length * step_duration, volume)
            current_pitch = note
            current_length = 1
            current_start = i
            
    # 写入最后一个音
    if current_pitch != 0:
        MyMIDI.addNote(track, channel_melody, current_pitch, 
                       current_start * step_duration, 
                       current_length * step_duration, volume)
            
    # --- 2. 写入背景和弦 (读取当前 config) ---
    for i, root in enumerate(config.CHORD_ROOTS):
        start_time = i * config.CHORD_DURATION
        # 简单的三和弦铺底
        # 简单处理：如果是 C 大调，根据根音构建自然三和弦
        # 这里为了通用性，直接构建 大三/小三 需要更复杂的逻辑，
        # 暂时保持简单的 0-4-7 (大三) 或 0-3-7 (小三) 可能会听起来怪。
        # 最稳妥的方法：构建调内三和弦 (Diatonic Triad)
        
        root_pc = root % 12
        # C大调音阶：0, 2, 4, 5, 7, 9, 11
        # 简单查表法构建 C 大调顺阶和弦
        # C(0):M, D(2):m, E(4):m, F(5):M, G(7):M, A(9):m, B(11):dim
        is_minor = root_pc in {2, 4, 9, 11} 
        third = 3 if is_minor else 4
        fifth = 6 if root_pc == 11 else 7 # Bdim 减五度
        
        MyMIDI.addNote(track, channel_chord, root, start_time, config.CHORD_DURATION, 60)
        MyMIDI.addNote(track, channel_chord, root+third, start_time, config.CHORD_DURATION, 60)
        MyMIDI.addNote(track, channel_chord, root+fifth, start_time, config.CHORD_DURATION, 60)

    with open(filename, "wb") as f:
        MyMIDI.writeFile(f)
    print(f"Saved MIDI to: {filename}")

def save_movement_to_midi(movement_melody, filename="movement_full.mid", tempo=80, chord_progression=None):
    """
    保存完整乐章 (优化版)
    """
    track = 0
    channel_melody = 0
    channel_chord = 1
    volume = 100
    step_duration = 1.0 / config.STEPS_PER_BEAT 
    
    MyMIDI = MIDIFile(1) 
    MyMIDI.addTempo(track, 0, tempo)
    
    # 1. 写入旋律 - 增加拆分概率逻辑
    if len(movement_melody) > 0:
        current_pitch = movement_melody[0]
        current_length = 1
        current_start = 0
    
        for i in range(1, len(movement_melody)):
            note = movement_melody[i]
            if note == current_pitch and note != 0:
                # 相同音高时，30%概率拆分，70%概率合并
                if random.random() < 0.3:
                    # 拆分当前音符
                    MyMIDI.addNote(track, channel_melody, current_pitch, 
                                   current_start * step_duration, 
                                   current_length * step_duration, volume)
                    # 开始新的音符计数
                    current_start = i
                    current_length = 1
                else:
                    # 继续合并
                    current_length += 1
            else:
                if current_pitch != 0:
                    MyMIDI.addNote(track, channel_melody, current_pitch, 
                                   current_start * step_duration, 
                                   current_length * step_duration, volume)
                current_pitch = note
                current_length = 1
                current_start = i
        if current_pitch != 0:
            MyMIDI.addNote(track, channel_melody, current_pitch, 
                           current_start * step_duration, 
                           current_length * step_duration, volume)
            
    # 2. 铺设和弦
    progression = chord_progression if chord_progression else config.CHORD_ROOTS
    total_beats = len(movement_melody) / config.STEPS_PER_BEAT
    
    current_beat = 0
    prog_idx = 0
    
    while current_beat < total_beats:
        root = progression[prog_idx % len(progression)]
        
        # 顺阶和弦逻辑
        root_pc = root % 12
        is_minor = root_pc in {2, 4, 9, 11}
        third = 3 if is_minor else 4
        fifth = 6 if root_pc == 11 else 7
        
        MyMIDI.addNote(track, channel_chord, root, current_beat, config.CHORD_DURATION, 55)
        MyMIDI.addNote(track, channel_chord, root+third, current_beat, config.CHORD_DURATION, 55)
        MyMIDI.addNote(track, channel_chord, root+fifth, current_beat, config.CHORD_DURATION, 55)
        
        current_beat += config.CHORD_DURATION
        prog_idx += 1

    with open(filename, "wb") as f:
        MyMIDI.writeFile(f)
    print(f"Movement saved to: {filename}")