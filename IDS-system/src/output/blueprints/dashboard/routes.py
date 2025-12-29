from flask import render_template, jsonify
from src.output.models.alert import Alert
from sqlalchemy import func
from src.app import db
from . import dash_bp

@dash_bp.route('/')
def index():
    return render_template('dashboard.html')

@dash_bp.route('/api/chart')
def chart_data():
    # 近 24h 趋势（按小时聚合）
    trend = db.session.query(
                func.strftime('%Y-%m-%d %H:00', Alert.event_time).label('h'),
                func.count(Alert.id).label('cnt')
            ).group_by('h').all()
    # 攻击类型饼图
    pie = db.session.query(Alert.attack_type,
                           func.count(Alert.id)).group_by(Alert.attack_type).all()
    return jsonify({'trend': [{'time':x.h, 'count':x.cnt} for x in trend],
                    'pie'  : [{'name':x[0], 'value':x[1]} for x in pie]})