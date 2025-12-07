# MusicAndMath/utils.py
import random
from midiutil import MIDIFile
import config

def generate_random_melody(length=config.TOTAL_STEPS):
    """根据配置生成随机基因"""
    melody = []
    for _ in range(length):
        if random.random() < config.REST_PROB:
            note = 0
        else:
            note = random.randint(config.PITCH_MIN, config.PITCH_MAX)
        melody.append(note)
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
    
    # --- 【关键修改】 动态计算步长 ---
    # 如果 STEPS_PER_BEAT=4, duration=0.25 (16分音符)
    # 如果 STEPS_PER_BEAT=2, duration=0.5 (8分音符)
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
            
    # --- 2. 写入背景和弦 ---
    for i, root in enumerate(config.CHORD_ROOTS):
        start_time = i * config.CHORD_DURATION
        # 和弦伴奏
        MyMIDI.addNote(track, channel_chord, root, start_time, config.CHORD_DURATION, 70)
        MyMIDI.addNote(track, channel_chord, root+4, start_time, config.CHORD_DURATION, 70)
        MyMIDI.addNote(track, channel_chord, root+7, start_time, config.CHORD_DURATION, 70)

    with open(filename, "wb") as f:
        MyMIDI.writeFile(f)
    print(f"Saved MIDI to: {filename}")

def save_movement_to_midi(movement_melody, filename="movement_full.mid", tempo=80, chord_progression=None):
    """
    保存完整乐章 (优化版)
    :param chord_progression: 可选，允许传入自定义的和弦走向列表，否则使用 config 默认值
    """
    track = 0
    channel_melody = 0
    channel_chord = 1
    volume = 100
    step_duration = 1.0 / config.STEPS_PER_BEAT 
    
    MyMIDI = MIDIFile(1) 
    MyMIDI.addTempo(track, 0, tempo)
    
    # 1. 写入旋律 (使用动态时值合并逻辑)
    if len(movement_melody) > 0:
        current_pitch = movement_melody[0]
        current_length = 1
        current_start = 0
    
        for i in range(1, len(movement_melody)):
            note = movement_melody[i]
            if note == current_pitch and note != 0:
                current_length += 1
            else:
                if current_pitch != 0:
                    MyMIDI.addNote(track, channel_melody, current_pitch, 
                                   current_start * step_duration, 
                                   current_length * step_duration, volume)
                current_pitch = note
                current_length = 1
                current_start = i
        # 最后一个音
        if current_pitch != 0:
            MyMIDI.addNote(track, channel_melody, current_pitch, 
                           current_start * step_duration, 
                           current_length * step_duration, volume)
            
    # 2. 铺设和弦
    # 使用传入的 progression 或者 config 默认的
    progression = chord_progression if chord_progression else config.CHORD_ROOTS
    
    # 计算总共有多少拍
    total_beats = len(movement_melody) / config.STEPS_PER_BEAT
    
    current_beat = 0
    prog_idx = 0
    
    while current_beat < total_beats:
        root = progression[prog_idx % len(progression)]
        
        # 简单的三和弦铺底
        MyMIDI.addNote(track, channel_chord, root, current_beat, config.CHORD_DURATION, 65)
        MyMIDI.addNote(track, channel_chord, root+4, current_beat, config.CHORD_DURATION, 65)
        MyMIDI.addNote(track, channel_chord, root+7, current_beat, config.CHORD_DURATION, 65)
        
        current_beat += config.CHORD_DURATION
        prog_idx += 1

    with open(filename, "wb") as f:
        MyMIDI.writeFile(f)
    print(f"Movement saved to: {filename} (Total steps: {len(movement_melody)})")