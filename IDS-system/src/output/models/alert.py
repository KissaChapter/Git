from datetime import datetime
from src.app import db

class Alert(db.Model):
    __tablename__ = 'alerts'
    id         = db.Column(db.Integer, primary_key=True)
    src_ip     = db.Column(db.String(45))
    dst_ip     = db.Column(db.String(45))
    attack_type= db.Column(db.String(50))
    severity   = db.Column(db.String(10))   # low/mid/high
    event_time = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def seed_demo():
        import random, itertools
        attacks = ['PortScan', 'DDoS', 'BruteForce']
        sevs    = ['low','mid','high']
        for _ in range(200):
            db.session.add(Alert(
                src_ip= f"10.0.0.{random.randint(1,254)}",
                dst_ip= f"192.168.1.{random.randint(1,254)}",
                attack_type=random.choice(attacks),
                severity=random.choice(sevs)))
        db.session.commit()

    @staticmethod
    def create_from_flow(row):
        """把 DataFrame 一行转成 Alert 入库"""
        db.session.add(Alert(
            src_ip=row['src_ip'],
            dst_ip=row['dst_ip'],
            attack_type='PortScan',  # 后续可再细分
            severity='high' if row['flow_pkts_s'] > 1000 else 'mid'
        ))
        db.session.commit()