# columns.py  ->  导出 41 维特征列名
import pyarrow.parquet as pq
import pathlib
import json

data_dir = pathlib.Path(__file__).with_name('data')
parquet_path = data_dir / 'NF-UQ-NIDS-v2.parquet'

try:
    schema = pq.read_schema(parquet_path)
    # 去掉最后 3 个标签列
    feature_cols = [name for name in schema.names if name not in {'Label', 'Attack', 'Dataset'}]

    print("=== 41 维特征列名 ===")
    for i, col in enumerate(feature_cols, 1):
        print(f"{i:2d}. '{col}'")

    # 直接生成 Python 列表代码，复制即可用
    print("\nPython 列表（复制到 model_services.py）:")
    print("MODEL_DIMS = [")
    for col in feature_cols:
        print(f"    '{col}',")
    print("]")

    # 顺手写进 columns.json（可选）
    (data_dir / 'columns.json').write_text(json.dumps(feature_cols))
    print("\n已写入 columns.json")

except Exception as e:
    print(f"错误: {e}")