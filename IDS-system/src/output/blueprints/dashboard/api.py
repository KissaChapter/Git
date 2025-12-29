# blueprints/dashboard/api.py
from flask import Blueprint, jsonify
import random, datetime

bp = Blueprint('dashboard_api', __name__, url_prefix='/api')

def random_trend():
    """生成 24h 每分钟随机数"""
    base = datetime.datetime.now()
    return [
        {"time": (base - datetime.timedelta(minutes=60*24-1-i)).strftime("%H:%M"),
         "count": random.randint(10, 200)}
        for i in range(60*24)
    ]

def random_pie():
    types = ['Normal', 'DoS', 'Probe', 'R2L', 'U2R']
    return [{"name": t, "value": random.randint(100, 1000)} for t in types]

@bp.route('/chart')
def chart():
    return jsonify({
        "trend": random_trend(),
        "pie":   random_pie()
    })