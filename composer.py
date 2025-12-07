# MusicAndMath/composer.py
from main import GAEngine
import utils
import config

def generate_symphony():
    print("========================================")
    print(" AI Composer: Starting Symphony Generation")
    print(" Structure: A (Theme) -> A' (Var) -> B (Contrast) -> A (Coda)")
    print("========================================")

    # 实例化引擎，可以为不同乐章使用不同的引擎参数
    # 比如 B 段可以使用更激进的变异率
    engine_standard = GAEngine(target_gens=300) 
    engine_creative = GAEngine(target_gens=200, mutation_rate=0.1) # 更有创造力

    # --- 1. Theme A (C大调，中音区) ---
    print("\n[Section 1] Composing Theme A...")
    theme_a = engine_standard.train()

    # --- 2. Variation A' (基于 A 变奏) ---
    print("\n[Section 2] Composing Variation A'...")
    # 减少代数，保留原汁原味
    engine_short = GAEngine(target_gens=50)
    theme_a_prime = engine_short.train(initial_seed=theme_a)

    # --- 3. Theme B (对比段：高音，情绪激昂) ---
    print("\n[Section 3] Composing Theme B (Contrast)...")
    # 使用 override 字典临时改变配置，而不是修改全局变量
    theme_b = engine_creative.train(
        constraints_override={
            'PITCH_MIN': 72, # 提高一个八度
            'PITCH_MAX': 96,
            'REST_PROB': 0.1 # 更密集，少休止
        }
    )

    # --- 4. Coda (A 的再现) ---
    print("\n[Section 4] Assembly Coda...")
    theme_a_coda = theme_a # 简单重复，也可以再次微调

    # --- 5. 组装与保存 ---
    full_movement = []
    # 可以在段落间加入休止符
    # full_movement.extend([0]*8) 
    full_movement.extend(theme_a)
    full_movement.extend(theme_a_prime)
    full_movement.extend(theme_b)
    full_movement.extend(theme_a_coda)

    output_file = "AI_Symphony_Movement_1.mid"
    # 这里可以根据需要传入特定的和弦走向，或者就用默认的
    utils.save_movement_to_midi(full_movement, output_file, tempo=96)
    print(f"Done! Saved to {output_file}")

if __name__ == "__main__":
    generate_symphony()