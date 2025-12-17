# MusicAndMath/composer.py
from main import GAEngine, get_user_chord_progression
import utils
import config

def generate_symphony():
    print("========================================")
    print(" AI Composer: Starting Symphony Generation")
    print(" Structure: A (Theme) -> A' (Var) -> B (Contrast) -> A (Coda)")
    print("========================================")
    
    # 询问用户是否要自定义全局和弦
    print("\n【全局设置】是否自定义 Theme A 的和弦走向?")
    chord_roots_A = get_user_chord_progression()
    
    override_A = {}
    if chord_roots_A:
        override_A['CHORD_ROOTS'] = chord_roots_A

    engine_standard = GAEngine(target_gens=300) 
    engine_creative = GAEngine(target_gens=200, mutation_rate=0.1) 

    # --- 1. Theme A ---
    print("\n[Section 1] Composing Theme A...")
    theme_a = engine_standard.train(constraints_override=override_A)

    # --- 2. Variation A' ---
    print("\n[Section 2] Composing Variation A'...")
    engine_short = GAEngine(target_gens=50)
    # A' 继承 A 的和弦配置
    theme_a_prime = engine_short.train(initial_seed=theme_a, constraints_override=override_A)

    # --- 3. Theme B ---
    print("\n[Section 3] Composing Theme B (Contrast)...")
    print("是否为 B 段自定义和弦? (回车跳过则使用默认)")
    chord_roots_B = get_user_chord_progression()
    
    override_B = {
        'PITCH_MIN': 72, 
        'PITCH_MAX': 96,
        'REST_PROB': 0.1
    }
    if chord_roots_B:
        override_B['CHORD_ROOTS'] = chord_roots_B
        
    theme_b = engine_creative.train(constraints_override=override_B)

    # --- 4. Coda ---
    print("\n[Section 4] Assembly Coda...")
    theme_a_coda = theme_a 

    # --- 5. 组装 ---
    full_movement = []
    full_movement.extend(theme_a)
    full_movement.extend(theme_a_prime)
    full_movement.extend(theme_b)
    full_movement.extend(theme_a_coda)

    output_file = "AI_Symphony_Movement_1.mid"
    
    # 保存时需要一个总的和弦走向来铺底，这里简单起见，拼合一下
    # 注意：save_movement_to_midi 里的逻辑是循环播放 progression
    # 所以为了精确对位，我们需要手动构造一个很长的 list
    
    final_progression = []
    # A 段和弦 (默认重复直到填满A段)
    roots_A = chord_roots_A if chord_roots_A else config.CHORD_ROOTS
    final_progression.extend(roots_A * 2) # 假设 A 和 A' 长度大概各占一轮
    
    # B 段和弦
    roots_B = chord_roots_B if chord_roots_B else config.CHORD_ROOTS
    final_progression.extend(roots_B)
    
    # Coda (A)
    final_progression.extend(roots_A)

    utils.save_movement_to_midi(full_movement, output_file, tempo=96, chord_progression=final_progression)
    print(f"Done! Saved to {output_file}")

if __name__ == "__main__":
    generate_symphony()