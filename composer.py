# MusicAndMath/composer.py
from main import GAEngine, get_user_chord_progression
import utils
import config

def generate_symphony():
    print(" AI Composer: Starting Symphony Generation")
    print(" Structure: A (Theme) -> A' (Var) -> B (Contrast) -> A (Coda)")
    print("\n【全局设置】是否自定义 Theme A 的和弦走向?")
    chord_roots_A = get_user_chord_progression()
    override_A = {}
    if chord_roots_A:
        override_A['CHORD_ROOTS'] = chord_roots_A
    engine_standard = GAEngine(target_gens=500) 
    engine_creative = GAEngine(target_gens=500, mutation_rate=0.1) 
    print("\n[Section 1] Composing Theme A...")
    theme_a = engine_standard.train(constraints_override=override_A)
    print("\n[Section 2] Composing Variation A'...")
    engine_var = GAEngine(target_gens=100, mutation_rate=0.2) 
    theme_a_prime = engine_var.train(initial_seed=theme_a, constraints_override=override_A)
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
    print("\n[Section 4] Assembly Coda...")
    theme_a_coda = theme_a 
    full_movement = []
    full_movement.extend(theme_a)
    full_movement.extend(theme_a_prime)
    full_movement.extend(theme_b)
    full_movement.extend(theme_a_coda)
    output_file = "AI_Symphony_Movement_1.mid"
    final_progression = []
    roots_A = chord_roots_A if chord_roots_A else config.CHORD_ROOTS
    final_progression.extend(roots_A * 2)
    roots_B = chord_roots_B if chord_roots_B else config.CHORD_ROOTS
    final_progression.extend(roots_B)
    final_progression.extend(roots_A)
    utils.save_movement_to_midi(full_movement, output_file, tempo=96, chord_progression=final_progression)
    print(f"Done! Saved to {output_file}")

if __name__ == "__main__":
    generate_symphony()