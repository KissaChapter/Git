import numpy as np
from collections import Counter

# 1. 加载标签
y_tr = np.load('./data/y_train.npy')
y_te = np.load('./data/y_test.npy')

# 2. 分层比例
print('===== 分层抽样检验 =====')
print(f'训练集总样本 {len(y_tr):,}')
print(f'测试集总样本 {len(y_te):,}')
print(f'训练集攻击比例 {y_tr.mean():.3%}')
print(f'测试集攻击比例 {y_te.mean():.3%}')
print(f'比例差 {abs(y_tr.mean() - y_te.mean()):.3%}  （< 2% 可认为分层 OK）')

# 3. 各类别分布
print('\n===== 训练集类别分布 =====')
for label, cnt in Counter(y_tr).items():
    print(f'class {label:>2}: {cnt:>8,}  ({cnt/len(y_tr):>6.2%})')

print('\n===== 测试集类别分布 =====')
for label, cnt in Counter(y_te).items():
    print(f'class {label:>2}: {cnt:>8,}  ({cnt/len(y_te):>6.2%})')

# 4. 数据泄露快速扫描（索引级）
print('\n===== 数据泄露扫描 =====')
# 如果训练/测试是同一次 split 的索引，这里会显示交集大小
# 若没有索引文件，可跳过；有则：
try:
    idx_tr = np.load('src/models/data/train_indices.npy')
    idx_te = np.load('src/models/data/test_indices.npy')
    leak = np.intersect1d(idx_tr, idx_te).size
    print(f'索引交集 {leak} 条  （应为 0）')
except FileNotFoundError:
    print('无 index 文件，跳过索引级泄露检查')