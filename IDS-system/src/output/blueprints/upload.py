import pandas as pd
import numpy as np
import os
from pathlib import Path
from flask import (
    Blueprint, request, redirect, url_for, flash,
    render_template, jsonify, Response, session
)
from sqlalchemy import insert
from werkzeug.security import generate_password_hash
from src.output.models.alert import Alert
from src.output.services.model_services import predict_df, scaler, MODEL_COLS
from src.app import db
from src.output.models.eval_ground_truth import EvalGroundTruth
from src.output.models.user import User
import random
import string
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont

bp = Blueprint('upload', __name__, url_prefix='/upload')
ALLOWED_EXT = {'.npy', '.csv'}
CHUNK_ROWS = 50_000

# 验证码生成函数
def generate_captcha():
    """生成验证码图片和文本"""
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    # 创建图片
    width, height = 120, 40
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 添加噪点
    for _ in range(100):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        draw.point((x, y), fill='black')
    
    # 绘制文字
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    for i, char in enumerate(captcha_text):
        x = 10 + i * 25 + random.randint(-5, 5)
        y = 5 + random.randint(-5, 5)
        draw.text((x, y), char, font=font, fill='black')
    
    # 转换为base64
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return captcha_text, f"data:image/png;base64,{img_str}"

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        captcha = request.form.get('captcha', '').upper()
        session_captcha = session.get('captcha', '').upper()
        
        # 验证验证码
        if not captcha or captcha != session_captcha:
            flash('验证码错误或已过期')
            return redirect(url_for('upload.register'))
        
        # 验证输入
        if not username or len(username) < 3:
            flash('用户名至少3个字符')
            return redirect(url_for('upload.register'))
        
        if not password or len(password) < 6:
            flash('密码至少6个字符')
            return redirect(url_for('upload.register'))
        
        if password != confirm_password:
            flash('两次密码输入不一致')
            return redirect(url_for('upload.register'))
        
        # 检查用户名是否存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('upload.register'))
        
        # 创建新用户
        try:
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()
            # 在注册成功的位置，确保使用绝对跳转
            flash('注册成功！请登录')
            return redirect(url_for('login'), code=302)
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请重试')
            return redirect(url_for('upload.register'))
    
    # GET请求：生成验证码
    captcha_text, captcha_image = generate_captcha()
    session['captcha'] = captcha_text
    
    return render_template('register.html', captcha_image=captcha_image)

@bp.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        return _handle_post()
    
    # 获取统计数据
    from src.output.models.alert import Alert
    total_alerts = Alert.query.count()
    
    return render_template('upload.html', 
                         total_flows=0,
                         attack_count=0,  # 改为0
                         accuracy=0)      # 改为0

def _handle_post():
    if 'flow_file' not in request.files:
        flash('请选择要上传的文件')
        return redirect(request.url)
    
    f = request.files['flow_file']
    if f.filename == '':
        flash('请选择文件')
        return redirect(request.url)
    
    ext = Path(f.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        flash('不支持的文件格式')
        return redirect(request.url)

    # 文件处理逻辑
    if ext == '.npy':
        df_iter = [pd.DataFrame(np.load(f))]
    else:
        df_iter = pd.read_csv(f, chunksize=CHUNK_ROWS)

    alert_queue = []
    eval_buffer = []
    total = 0

    for chunk in df_iter:
        chunk = chunk[MODEL_COLS]
        chunk['pred'] = predict_df(chunk)
        
        # 收集评估数据
        for _, row in chunk.iterrows():
            eval_buffer.append({
                'batch_tag': f.filename,
                'true_label': int(row.get('label', 0)),
                'pred_label': int(row.get('pred', 0))
            })
        
        attacks = chunk[chunk['pred'] == 1]
        for _, row in attacks.iterrows():
            alert_queue.append({
                'src_ip': str(row.get('src_ip', '0.0.0.0')),
                'dst_ip': str(row.get('dst_ip', '0.0.0.0')),
                'attack_type': str(row.get('attack_type', 'Unknown')),
                'severity': int(row.get('severity', 1)),
                'event_time': pd.Timestamp.now()
            })
        
        total += len(chunk)
        
        if len(alert_queue) >= 10_000:
            _flush_alerts(alert_queue)
            alert_queue.clear()

    if alert_queue:
        _flush_alerts(alert_queue)

    # 写入评估数据
    if eval_buffer:
        db.session.execute(insert(EvalGroundTruth), eval_buffer)
        db.session.commit()
    
    flash(f'分析完成！共处理 {total:,} 条流，可疑流已写入 Alert 表')
    return redirect(url_for('dashboard.index'))

def _flush_alerts(records):
    """批量插入 Alert"""
    if not records:
        return
    db.session.execute(insert(Alert), records)
    db.session.commit()