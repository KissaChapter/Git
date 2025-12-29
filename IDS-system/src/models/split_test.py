#!/usr/bin/env python3
# split_test_half.py - 把原 test 集随机 50/50 分层切成 A/B 两半
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split

# ========== 配置 ==========
data_dir   = Path(__file__).parent.parent / 'models' /'data'   # 指向 data 文件夹
random_state = 42         # 固定随机种子，保证复现
# ==========================

def main():
    print("=== 把原 test 集 50/50 分层切成 A/B 两半 ===")
    # 1. 加载原 test 集（只读，不动原文件）
    X_test = np.load(data_dir / 'X_test.npy', mmap_mode='r')
    y_test = np.load(data_dir / 'y_test.npy', mmap_mode='r')
    print(f"原 test 集: X{X_test.shape}, y{y_test.shape}")

    # 2. 分层随机 50/50 切
    X_A, X_B, y_A, y_B = train_test_split(
        X_test, y_test,
        test_size=0.5,               # 一半给 B
        stratify=y_test,
        random_state=random_state
    )

    # 3. 保存为内存映射（不压缩，方便后续流式读）
    for split, X, y in [('half_A', X_A, y_A), ('half_B', X_B, y_B)]:
        print(f"\n{split} -> X{X.shape}, y{y.shape}")
        # 标签分布
        normal = np.sum(y == 0)
        attack = np.sum(y == 1)
        print(f"  正常: {normal:,} ({normal / len(y) * 100:.2f}%)")
        print(f"  异常: {attack:,} ({attack / len(y) * 100:.2f}%)")

        # 写出 .npy（内存映射）
        X_mmap = np.lib.format.open_memmap(
            data_dir / f'X_test_{split}.npy', mode='w+',
            dtype='float32', shape=X.shape
        )
        y_mmap = np.lib.format.open_memmap(
            data_dir / f'y_test_{split}.npy', mode='w+',
            dtype='int32', shape=y.shape
        )
        X_mmap[:] = X
        y_mmap[:] = y
        X_mmap.flush(); y_mmap.flush()
        print(f"  已保存: X_test_{split}.npy / y_test_{split}.npy")

    print("\n=== 切分完成 ===")

if __name__ == '__main__':
    main()