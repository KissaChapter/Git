
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from src.config import Config


db = SQLAlchemy()

def create_app():
    app = Flask(__name__, static_folder='output/static', template_folder='output/templates')
    app.config.from_object(Config)
    db.init_app(app)

    # 一次性导入并注册
    from src.output.blueprints.dashboard import dash_bp
    from src.output.blueprints.report.routes import bp as rep_bp
    from src.output.blueprints.upload import bp as upload_bp

    app.register_blueprint(dash_bp)
    app.register_blueprint(rep_bp)
    app.register_blueprint(upload_bp)

    # 添加根路径重定向到登录页面
    @app.route('/')
    def index():
        return redirect(url_for('login'))  # 已经是正确的配置

    # 修改后的登录路由 - 使用模板文件
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # 从数据库查询用户
            from src.output.models.user import User
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                return redirect(url_for('upload.upload'))
            else:
                return render_template('login.html', error='用户名或密码错误')
        
        return render_template('login.html')


    with app.app_context():
        db.create_all()
        if Config.DEMO_MODE:
            from src.output.models.alert import Alert
            Alert.seed_demo()
            
            # 创建默认管理员账号
            from src.output.models.user import User
            from werkzeug.security import generate_password_hash
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    password_hash=generate_password_hash('password123')
                )
                db.session.add(admin_user)
                db.session.commit()
    return app