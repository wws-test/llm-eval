# API蓝图包初始化文件
from flask import Blueprint

# 创建API主蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 导入所有API子模块
from app.routes.api import auth_api, models_api, datasets_api, chat_api, eval_api, stats_api, performance_api

# 注册子蓝图
api_bp.register_blueprint(auth_api.bp)
api_bp.register_blueprint(models_api.bp)
api_bp.register_blueprint(datasets_api.bp)
api_bp.register_blueprint(chat_api.bp)
api_bp.register_blueprint(eval_api.bp)
api_bp.register_blueprint(stats_api.bp)
api_bp.register_blueprint(performance_api.bp)
