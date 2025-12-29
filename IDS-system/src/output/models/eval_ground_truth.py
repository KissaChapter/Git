from src.app import db
from datetime import datetime

class EvalGroundTruth(db.Model):
    __tablename__ = 'eval_ground_truth'
    id          = db.Column(db.Integer, primary_key=True)
    batch_tag   = db.Column(db.String(64), index=True)   # 批次号=上传文件名
    true_label  = db.Column(db.Integer, nullable=False)  # 0/1
    pred_label  = db.Column(db.Integer, nullable=False)  # 0/1
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)