# npy2csv_stream.py - 流式 .npy → .csv 转换（零内存）
import numpy as np
import pandas as pd
from pathlib import Path
import tqdm

# ========== 配置 ==========
data_dir   = Path(__file__).parent.parent / 'models' /'data'   # 指向 data 文件夹
feature_cols = [
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
# ==========================


def npy2csv(X_path, y_path, csv_path, chunk_rows=100_000):
    """流式转换"""
    print(f"\n转换: {X_path.name} + {y_path.name} → {csv_path.name}")
    X = np.load(X_path, mmap_mode='r')   # 只读映射
    y = np.load(y_path, mmap_mode='r')
    total_rows = X.shape[0]
    print(f"总样本: {total_rows:,} | chunk: {chunk_rows:,}")

    # 提前打开 CSV 文件，写表头
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(','.join(feature_cols) + ',Label\n')

        # 按 chunk 逐块写入
        for start in tqdm.trange(0, total_rows, chunk_rows, desc='CSV 写入'):
            end = min(start + chunk_rows, total_rows)
            df_chunk = pd.DataFrame(X[start:end], columns=feature_cols)
            df_chunk['Label'] = y[start:end]
            # 不带索引，追加写入
            df_chunk.to_csv(f, index=False, header=False, lineterminator='\n')
            del df_chunk      # 立即释放

    print(f"完成！→ {csv_path}")


def main():
    data_dir = Path(__file__).parent.parent / 'models' /'data'
    # 可批量转多个 split
    for split in ['half_A', 'half_B']:       # 要转化的文件名
        X_file = data_dir / f'X_test_{split}.npy'
        y_file = data_dir / f'y_test_{split}.npy'
        csv_file = data_dir / f'test_{split}.csv'
        if X_file.exists() and y_file.exists():
            npy2csv(X_file, y_file, csv_file, chunk_rows=100_000)
        else:
            print(f"跳过 {split} -> 文件不存在")


if __name__ == '__main__':
    main()