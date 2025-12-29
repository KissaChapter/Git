import pandas as pd
import os

SRC_FILE   = 'data/test_half_A.csv'
OUT_DIR    = 'data/A_csv'
SAMPLE_PCT = 0.05          # 每份 5 %
PARTS      = 20            # 20 份独立子集

os.makedirs(OUT_DIR, exist_ok=True)

print('正在读取原文件…')
df = pd.read_csv(SRC_FILE)
print(f'原文件 {len(df):,} 行')

print('正在生成 20 份独立 5 % 随机子集…')
for i in range(PARTS):
    tmp = df.sample(frac=SAMPLE_PCT, random_state=i)   # 不同种子 → 不同子集
    out_path = os.path.join(OUT_DIR, f'A_{i:02d}.csv')
    tmp.to_csv(out_path, index=False)
    print(f'A_{i:02d}.csv  已写出  {len(tmp):,} 行')

print('完成！文件列表：')
print([os.path.join(OUT_DIR, f'A_{i:02d}.csv') for i in range(PARTS)])