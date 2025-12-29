# src/output/blueprints/dashboard/__init__.py
from flask import Blueprint

dash_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# 先挂 API 子蓝图
from .api import bp as api_bp
dash_bp.register_blueprint(api_bp, url_prefix='/api')

# 再注册页面路由
from . import routes