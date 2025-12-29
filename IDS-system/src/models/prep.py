# prep_stratified.py - 分层抽样预处理
import pyarrow.parquet as pq
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import pathlib
import gc

# 配置
data_dir = pathlib.Path(__file__).parent / 'data'
parquet_path = data_dir / 'NF-UQ-NIDS-v2.parquet'
batch_size = 50000
test_ratio = 0.2  # 20%测试集
random_seed = 42

# 特征列
feature_columns = [
    'L4_SRC_PORT', 'L4_DST_PORT', 'PROTOCOL', 'L7_PROTO', 'IN_BYTES',
    'IN_PKTS', 'OUT_BYTES', 'OUT_PKTS', 'TCP_FLAGS', 'CLIENT_TCP_FLAGS',
    'SERVER_TCP_FLAGS', 'FLOW_DURATION_MILLISECONDS', 'DURATION_IN',
    'DURATION_OUT', 'MIN_TTL', 'MAX_TTL', 'LONGEST_FLOW_PKT',
    'SHORTEST_FLOW_PKT', 'MIN_IP_PKT_LEN', 'MAX_IP_PKT_LEN',
    'SRC_TO_DST_SECOND_BYTES', 'DST_TO_SRC_SECOND_BYTES',
    'RETRANSMITTED_IN_BYTES', 'RETRANSMITTED_IN_PKTS',
    'RETRANSMITTED_OUT_BYTES', 'RETRANSMITTED_OUT_PKTS',
    'SRC_TO_AVG_THROUGHPUT', 'DST_TO_SRC_AVG_THROUGHPUT',
    'NUM_PKTS_UP_TO_128_BYTES', 'NUM_PKTS_128_TO_256_BYTES',
    'NUM_PKTS_256_TO_512_BYTES', 'NUM_PKTS_512_TO_1024_BYTES',
    'NUM_PKTS_1024_TO_1514_BYTES', 'TCP_WIN_MAX_IN', 'TCP_WIN_MAX_OUT',
    'ICMP_TYPE', 'ICMP_IPV4_TYPE', 'DNS_QUERY_ID', 'DNS_QUERY_TYPE',
    'DNS_TTL_ANSWER', 'FTP_COMMAND_RET_CODE'
]


def count_class_distribution():
    """统计类别分布"""
    print("步骤1: 统计类别分布...")
    parquet = pq.ParquetFile(parquet_path)

    normal_count = 0
    attack_count = 0
    total_count = 0

    for batch in parquet.iter_batches(batch_size=batch_size):
        df = batch.to_pandas()
        labels = df['Label'].values
        normal_count += np.sum(labels == 0)
        attack_count += np.sum(labels == 1)
        total_count += len(labels)

        del df, labels
        if total_count % 100000 == 0:
            print(f"  已统计 {total_count:,} 样本")
        gc.collect()

    print(f"\n总样本数: {total_count:,}")
    print(f"正常样本: {normal_count:,} ({normal_count / total_count * 100:.2f}%)")
    print(f"异常样本: {attack_count:,} ({attack_count / total_count * 100:.2f}%)")

    return normal_count, attack_count, total_count


def create_stratified_indices(normal_count, attack_count, total_count):
    """创建分层抽样索引"""
    print("\n步骤2: 创建分层抽样索引...")

    np.random.seed(random_seed)

    # 计算每个类别的测试集数量
    normal_test_size = int(normal_count * test_ratio)
    attack_test_size = int(attack_count * test_ratio)

    print(f"训练集目标: 正常={normal_count - normal_test_size:,}, 异常={attack_count - attack_test_size:,}")
    print(f"测试集目标: 正常={normal_test_size:,}, 异常={attack_test_size:,}")

    # 生成测试集索引（每个类别随机选择）
    parquet = pq.ParquetFile(parquet_path)

    normal_indices = []
    attack_indices = []
    current_idx = 0

    print("收集样本索引...")
    for batch in parquet.iter_batches(batch_size=batch_size):
        df = batch.to_pandas()
        labels = df['Label'].values
        batch_size_actual = len(labels)

        # 记录当前批次中每个类别的索引
        batch_normal = np.where(labels == 0)[0] + current_idx
        batch_attack = np.where(labels == 1)[0] + current_idx

        normal_indices.extend(batch_normal)
        attack_indices.extend(batch_attack)

        current_idx += batch_size_actual

        if current_idx % 100000 == 0:
            print(f"  已处理 {current_idx:,} 样本")

        del df, labels
        gc.collect()

    # 随机打乱并分割
    normal_indices = np.array(normal_indices)
    attack_indices = np.array(attack_indices)

    np.random.shuffle(normal_indices)
    np.random.shuffle(attack_indices)

    # 分割测试集和训练集索引
    test_indices = np.concatenate([
        normal_indices[:normal_test_size],
        attack_indices[:attack_test_size]
    ])

    train_indices = np.concatenate([
        normal_indices[normal_test_size:],
        attack_indices[attack_test_size:]
    ])

    # 保存索引
    np.save(data_dir / 'train_indices.npy', train_indices)
    np.save(data_dir / 'test_indices.npy', test_indices)

    print(f"\n索引创建完成:")
    print(f"训练集索引: {len(train_indices):,}")
    print(f"测试集索引: {len(test_indices):,}")

    return train_indices, test_indices


import pyarrow.parquet as pq
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import pathlib
import gc
import json

# ===================== 同 prep.py 配置 =====================
data_dir       = pathlib.Path(__file__).parent / 'data'
parquet_path   = data_dir / 'NF-UQ-NIDS-v2.parquet'
batch_size     = 50000
test_ratio     = 0.2
random_seed    = 42
feature_columns= [
    'L4_SRC_PORT', 'L4_DST_PORT', 'PROTOCOL', 'L7_PROTO', 'IN_BYTES',
    'IN_PKTS', 'OUT_BYTES', 'OUT_PKTS', 'TCP_FLAGS', 'CLIENT_TCP_FLAGS',
    'SERVER_TCP_FLAGS', 'FLOW_DURATION_MILLISECONDS', 'DURATION_IN',
    'DURATION_OUT', 'MIN_TTL', 'MAX_TTL', 'LONGEST_FLOW_PKT',
    'SHORTEST_FLOW_PKT', 'MIN_IP_PKT_LEN', 'MAX_IP_PKT_LEN',
    'SRC_TO_DST_SECOND_BYTES', 'DST_TO_SRC_SECOND_BYTES',
    'RETRANSMITTED_IN_BYTES', 'RETRANSMITTED_IN_PKTS',
    'RETRANSMITTED_OUT_BYTES', 'RETRANSMITTED_OUT_PKTS',
    'SRC_TO_DST_AVG_THROUGHPUT', 'DST_TO_SRC_AVG_THROUGHPUT',
    'NUM_PKTS_UP_TO_128_BYTES', 'NUM_PKTS_128_TO_256_BYTES',
    'NUM_PKTS_256_TO_512_BYTES', 'NUM_PKTS_512_TO_1024_BYTES',
    'NUM_PKTS_1024_TO_1514_BYTES', 'TCP_WIN_MAX_IN', 'TCP_WIN_MAX_OUT',
    'ICMP_TYPE', 'ICMP_IPV4_TYPE', 'DNS_QUERY_ID', 'DNS_QUERY_TYPE',
    'DNS_TTL_ANSWER', 'FTP_COMMAND_RET_CODE'
]
# =========================================================

def train_scaler(train_indices):
    """步骤3：在训练集上训练标准化器"""
    print("\n步骤3: 在训练集上训练标准化器...")
    scaler = StandardScaler()
    train_indices_set = set(train_indices)
    parquet = pq.ParquetFile(parquet_path)
    current_idx   = 0
    samples_used  = 0

    for batch in parquet.iter_batches(batch_size=batch_size):
        df = batch.to_pandas()
        batch_size_actual = len(df)
        batch_indices = np.arange(current_idx, current_idx + batch_size_actual)
        mask = np.array([idx in train_indices_set for idx in batch_indices])

        if np.any(mask):
            x = df.loc[mask, feature_columns].values.astype('float64')
            scaler.partial_fit(x)
            samples_used += np.sum(mask)
            del x
        current_idx += batch_size_actual
        if current_idx % 100_000 == 0:
            print(f"  已处理 {current_idx:,} 样本 (训练样本: {samples_used:,})")
        del df
        gc.collect()

    joblib.dump(scaler, data_dir / 'scaler.gz')
    print(f"标准化器训练完成，使用 {samples_used:,} 个训练样本")
    return scaler


def process_and_save_batches(scaler, train_indices, test_indices):
    """步骤4：处理并保存批次文件"""
    print("\n步骤4: 处理并保存批次文件...")

    train_dir = data_dir / 'temp_train'
    test_dir  = data_dir / 'temp_test'
    train_dir.mkdir(exist_ok=True)
    test_dir.mkdir(exist_ok=True)

    train_indices_set = set(train_indices)
    test_indices_set  = set(test_indices)
    parquet = pq.ParquetFile(parquet_path)
    current_idx        = 0
    train_batch_count  = 0
    test_batch_count   = 0

    for batch in parquet.iter_batches(batch_size=batch_size):
        df = batch.to_pandas()
        batch_size_actual = len(df)
        batch_indices = np.arange(current_idx, current_idx + batch_size_actual)
        train_mask = np.array([idx in train_indices_set for idx in batch_indices])
        test_mask  = np.array([idx in test_indices_set  for idx in batch_indices])

        # ---- 训练集 ----
        if np.any(train_mask):
            x_train = np.zeros((np.sum(train_mask), len(feature_columns)), dtype='float32')
            for j, col in enumerate(feature_columns):
                col_data = df.loc[train_mask, col].values.astype('float64')
                x_train[:, j] = ((col_data - scaler.mean_[j]) / scaler.scale_[j]).astype('float32')
            y_train = df.loc[train_mask, 'Label'].values.astype('int32')
            np.save(train_dir / f'X_batch_{train_batch_count:06d}.npy', x_train)
            np.save(train_dir / f'y_batch_{train_batch_count:06d}.npy', y_train)
            train_batch_count += 1
            del x_train, y_train

        # ---- 测试集 ----
        if np.any(test_mask):
            x_test = np.zeros((np.sum(test_mask), len(feature_columns)), dtype='float32')
            for j, col in enumerate(feature_columns):
                col_data = df.loc[test_mask, col].values.astype('float64')
                x_test[:, j] = ((col_data - scaler.mean_[j]) / scaler.scale_[j]).astype('float32')
            y_test = df.loc[test_mask, 'Label'].values.astype('int32')
            np.save(test_dir / f'X_batch_{test_batch_count:06d}.npy', x_test)
            np.save(test_dir / f'y_batch_{test_batch_count:06d}.npy', y_test)
            test_batch_count += 1
            del x_test, y_test

        current_idx += batch_size_actual
        if current_idx % 100_000 == 0:
            print(f"  已处理 {current_idx:,} 样本 (训练批次: {train_batch_count}, 测试批次: {test_batch_count})")
        del df
        gc.collect()

    # ---- 元数据 ----
    metadata = {
        'train_batches': train_batch_count,
        'test_batches': test_batch_count,
        'feature_count': len(feature_columns),
        'test_ratio': test_ratio,
        'random_seed': random_seed
    }
    with open(data_dir / 'split_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n批次文件保存完成:")
    print(f"训练集批次: {train_batch_count}")
    print(f"测试集批次: {test_batch_count}")
    return train_batch_count, test_batch_count


# ===================== 主入口 =====================
if __name__ == "__main__":
    print("开始分层抽样预处理...")
    print(f"批次大小: {batch_size}")
    print(f"测试集比例: {test_ratio}")
    print(f"随机种子: {random_seed}")

    # 执行流程
    normal_count, attack_count, total_count = count_class_distribution()
    train_indices, test_indices = create_stratified_indices(normal_count, attack_count, total_count)

    print("\n步骤1-2完成!")

    print("=== 步骤 3+ 独立运行 ===")
    # 复用步骤 1/2 产出的索引
    train_indices = np.load(data_dir / 'train_indices.npy')
    test_indices  = np.load(data_dir / 'test_indices.npy')
    print(f"加载索引完成 | 训练: {len(train_indices):,} | 测试: {len(test_indices):,}")

    scaler = train_scaler(train_indices)
    train_batches, test_batches = process_and_save_batches(scaler, train_indices, test_indices)

    print("\n步骤 3+ 完成！")