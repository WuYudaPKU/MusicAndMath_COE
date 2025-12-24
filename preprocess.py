import pretty_midi
import numpy as np
import os
import torch

def midi_to_sequence(midi_path, steps_per_bar=8, num_bars=4):
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        melody_track = None
        for inst in midi_data.instruments:
            if not inst.is_drum:
                melody_track = inst
                break
        
        if not melody_track: return None

        total_steps = steps_per_bar * num_bars
        #fs = 1.0 / (midi_data.get_beats()[1] / 2)
        fs=8
        piano_roll = melody_track.get_piano_roll(fs=fs)
        
        sequence = []
        last_pitch = -1
        
        for t in range(min(total_steps, piano_roll.shape[1])):
            notes = np.nonzero(piano_roll[:, t])[0]
            if len(notes) == 0:
                sequence.append(0)
                last_pitch = -1
            else:
                current_pitch = notes[-1]
                if current_pitch == last_pitch:
                    sequence.append(128)
                else:
                    sequence.append(current_pitch)
                    last_pitch = current_pitch
        while len(sequence) < total_steps:
            sequence.append(0)
        return sequence[:total_steps]
    except:
        return None

def preprocess_recursive(root_path, save_name):
    data = []
    print(f"正在从 {root_path} 扫描 MIDI 文件...")
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith((".mid", ".midi")):
                full_path = os.path.join(root, file)
                seq = midi_to_sequence(full_path)
                if seq:
                    data.append(seq)
    
    if data:
        torch.save(torch.LongTensor(data), save_name)
        print(f"成功预处理 {len(data)} 条序列并保存至 {save_name}")
    else:
        print("未找到有效数据，请检查路径")

if __name__ == "__main__":
    preprocess_recursive("data/lmd/clean_midi", "clean_midi_dataset.pt")