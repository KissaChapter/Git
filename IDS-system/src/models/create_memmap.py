# create_memmap_stratified.py - 创建分离的训练集和测试集内存映射
import numpy as np
from pathlib import Path
import json


def create_memmap_for_split(data_dir, split_name):
    """为训练集或测试集创建内存映射"""
    temp_dir = data_dir / f'temp_{split_name}'

    print(f"\n创建{split_name}集内存映射...")

    # 计算总样本数
    print(f"计算{split_name}集大小...")
    total_samples = 0
    sample_shape = None

    batch_files = list(temp_dir.glob('X_batch_*.npy'))
    total_batches = len(batch_files)

    if total_batches == 0:
        print(f"错误: {temp_dir} 中没有找到批次文件!")
        return None

    for i in range(total_batches):
        X_batch = np.load(temp_dir / f'X_batch_{i:06d}.npy', mmap_mode='r')
        total_samples += X_batch.shape[0]
        if sample_shape is None:
            sample_shape = X_batch.shape[1]
        del X_batch

    print(f"{split_name}集: {total_samples:,} 样本, {sample_shape} 特征")

    # 创建内存映射文件
    X_final = np.lib.format.open_memmap(
        data_dir / f'X_{split_name}.npy', mode='w+', dtype='float32',
        shape=(total_samples, sample_shape)
    )
    y_final = np.lib.format.open_memmap(
        data_dir / f'y_{split_name}.npy', mode='w+', dtype='int32',
        shape=(total_samples,)
    )

    # 逐批次写入
    current_idx = 0
    print(f"合并{split_name}集数据...")

    for i in range(total_batches):
        X_batch = np.load(temp_dir / f'X_batch_{i:06d}.npy', mmap_mode='r')
        y_batch = np.load(temp_dir / f'y_batch_{i:06d}.npy', mmap_mode='r')

        batch_size = X_batch.shape[0]
        X_final[current_idx:current_idx + batch_size] = X_batch
        y_final[current_idx:current_idx + batch_size] = y_batch
        current_idx += batch_size

        if i % 500 == 0:
            print(f"  进度: {i}/{total_batches} ({i / total_batches * 100:.1f}%)")

        del X_batch, y_batch

    # 刷新到磁盘
    X_final.flush()
    y_final.flush()

    print(f"{split_name}集完成! 共 {current_idx:,} 样本")

    # 验证
    X_verify = np.load(data_dir / f'X_{split_name}.npy', mmap_mode='r')
    y_verify = np.load(data_dir / f'y_{split_name}.npy', mmap_mode='r')
    print(f"验证: X{X_verify.shape}, y{y_verify.shape}")

    normal_count = np.sum(y_verify == 0)
    attack_count = np.sum(y_verify == 1)
    print(f"标签分布: 正常={normal_count:,} ({normal_count / len(y_verify) * 100:.2f}%), "
          f"异常={attack_count:,} ({attack_count / len(y_verify) * 100:.2f}%)")

    return {
        'samples': current_idx,
        'features': sample_shape,
        'normal': int(normal_count),
        'attack': int(attack_count)
    }


def main():
    data_dir = Path(__file__).parent / 'data'

    # 检查必需文件
    metadata_file = data_dir / 'split_metadata.json'
    if not metadata_file.exists():
        print("错误: 找不到 split_metadata.json")
        print("请先运行: python prep_stratified.py")
        return

    # 加载元数据
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    print("=" * 60)
    print("创建分层抽样的内存映射文件")
    print("=" * 60)
    print(f"测试集比例: {metadata['test_ratio']}")
    print(f"随机种子: {metadata['random_seed']}")

    # 检查临时目录
    train_dir = data_dir / 'temp_train'
    test_dir = data_dir / 'temp_test'

    # 创建训练集内存映射
    train_stats = create_memmap_for_split(data_dir, 'train')
    if train_stats is None:
        print("\n训练集创建失败，程序终止")
        return

    # 创建测试集内存映射
    test_stats = create_memmap_for_split(data_dir, 'test')
    if test_stats is None:
        print("\n测试集创建失败，程序终止")
        return

    # 汇总统计
    print("\n" + "=" * 60)
    print("数据集创建完成!")
    print("=" * 60)

    total_samples = train_stats['samples'] + test_stats['samples']
    total_normal = train_stats['normal'] + test_stats['normal']
    total_attack = train_stats['attack'] + test_stats['attack']

    print(f"\n总计: {total_samples:,} 样本")
    print(f"  正常: {total_normal:,} ({total_normal / total_samples * 100:.2f}%)")
    print(f"  异常: {total_attack:,} ({total_attack / total_samples * 100:.2f}%)")

    print(f"\n训练集: {train_stats['samples']:,} 样本 ({train_stats['samples'] / total_samples * 100:.2f}%)")
    print(f"  正常: {train_stats['normal']:,} ({train_stats['normal'] / train_stats['samples'] * 100:.2f}%)")
    print(f"  异常: {train_stats['attack']:,} ({train_stats['attack'] / train_stats['samples'] * 100:.2f}%)")

    print(f"\n测试集: {test_stats['samples']:,} 样本 ({test_stats['samples'] / total_samples * 100:.2f}%)")
    print(f"  正常: {test_stats['normal']:,} ({test_stats['normal'] / test_stats['samples'] * 100:.2f}%)")
    print(f"  异常: {test_stats['attack']:,} ({test_stats['attack'] / test_stats['samples'] * 100:.2f}%)")

    # 验证分层是否正确
    train_attack_ratio = train_stats['attack'] / train_stats['samples']
    test_attack_ratio = test_stats['attack'] / test_stats['samples']
    ratio_diff = abs(train_attack_ratio - test_attack_ratio)

    print(f"\n分层验证:")
    print(f"  训练集异常比例: {train_attack_ratio * 100:.3f}%")
    print(f"  测试集异常比例: {test_attack_ratio * 100:.3f}%")
    print(f"  比例差异: {ratio_diff * 100:.3f}%")

    if ratio_diff < 0.01:
        print("  ✓ 分层抽样成功，类别比例一致")
    else:
        print("  ⚠ 警告: 类别比例差异较大")

    # 更新元数据
    metadata['train_stats'] = train_stats
    metadata['test_stats'] = test_stats

    with open(data_dir / 'split_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)


if __name__ == "__main__":
    main()