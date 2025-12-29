import os
class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ids.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)
    DEMO_MODE = True          # True=演示数据  False=生产模型