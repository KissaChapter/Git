import joblib, json, pandas as pd
from pathlib import Path
import lightgbm as lgb
import warnings, sklearn.exceptions
warnings.filterwarnings("ignore", category=sklearn.exceptions.InconsistentVersionWarning)

SRC_ROOT   = Path(__file__).resolve().parents[2]
SCALER_PATH= SRC_ROOT / 'models' / 'data' / 'scaler.gz'
COL_PATH   = SRC_ROOT / 'models' / 'data' / 'columns.json'

# 1. 用 LightGBM 自带接口加载文本模型
clf = lgb.Booster(model_file=str(SRC_ROOT / 'models' /'data' / 'lightgbm_model.txt'))

scaler = joblib.load(SCALER_PATH)
with open(COL_PATH) as f:
    MODEL_COLS = json.load(f)

def predict_df(df: pd.DataFrame) -> pd.Series:
    df = df[MODEL_COLS]
    X = scaler.transform(df)
    # 2. 预测概率 > 0.5 视为 1
    y_score = clf.predict(X)
    return pd.Series((y_score > 0.5).astype(int), index=df.index, name='pred')