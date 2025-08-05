#!/usr/bin/env python3
"""
简单的API启动脚本
"""

import os
import sys
from flask import Flask
from flask_cors import CORS

def create_simple_app():
    """创建简单的Flask应用"""
    app = Flask(__name__)
    
    # 基础配置
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///simple_llm_eval.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # 启用CORS
    CORS(app, origins=['http://localhost:3000', 'http://localhost:4000'])
    
    # 初始化扩展
    from app import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)
    
    # 注册API蓝图
    from app.routes.api.models_api import bp as models_bp
    from app.routes.api.datasets_api import bp as datasets_bp
    from app.routes.api.chat_api import bp as chat_bp
    from app.routes.api.eval_api import bp as eval_bp
    from app.routes.api.stats_api import bp as stats_bp
    
    app.register_blueprint(models_bp, url_prefix='/api/models')
    app.register_blueprint(datasets_bp, url_prefix='/api/datasets')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(eval_bp, url_prefix='/api/evaluations')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    
    @app.route('/health')
    def health():
        return {'status': 'ok', 'message': 'API服务正常'}
    
    @app.route('/')
    def index():
        return {'message': 'LLM评估平台API服务', 'version': '1.0.0'}
    
    return app

def init_simple_database(app):
    """初始化数据库"""
    with app.app_context():
        from app import db
        from app.models import User, AIModel, Dataset
        
        # 创建数据库表
        db.create_all()
        print("✅ 数据库表创建成功")
        
        # 创建基础数据
        if User.query.count() == 0:
            print("📝 初始化基础数据...")
            
            # 创建管理员用户
            admin_user = User(username='admin')
            admin_user.set_password('admin')
            db.session.add(admin_user)
            
            # 创建系统模型
            system_models = [
                AIModel(
                    display_name='GPT-4o',
                    model_identifier='gpt-4o',
                    provider_name='OpenAI',
                    model_type='openai_compatible',
                    api_base_url='https://api.openai.com/v1',
                    is_system_model=True,
                    is_validated=True,
                    default_temperature=0.7,
                    system_prompt='You are a helpful assistant.'
                ),
                AIModel(
                    display_name='Claude-3 Opus',
                    model_identifier='claude-3-opus-20240229',
                    provider_name='Anthropic',
                    model_type='openai_compatible',
                    api_base_url='https://api.anthropic.com/v1',
                    is_system_model=True,
                    is_validated=True,
                    default_temperature=0.7,
                    system_prompt='You are Claude, an AI assistant created by Anthropic.'
                ),
                AIModel(
                    display_name='Qwen2.5-72B-Instruct',
                    model_identifier='qwen/Qwen2.5-72B-Instruct',
                    provider_name='ModelScope',
                    model_type='openai_compatible',
                    api_base_url='https://api-inference.modelscope.cn/v1',
                    is_system_model=True,
                    is_validated=True,
                    default_temperature=0.7,
                    system_prompt='You are Qwen, created by Alibaba Cloud.'
                )
            ]
            
            for model in system_models:
                db.session.add(model)
            
            db.session.commit()
            print("✅ 基础数据初始化完成!")
            print(f"   - 管理员账户: admin/admin")
            print(f"   - 系统模型: {len(system_models)}个")

if __name__ == '__main__':
    print("🚀 启动简单API服务...")
    
    # 创建应用
    app = create_simple_app()
    
    # 初始化数据库
    init_simple_database(app)
    
    print("🚀 启动API开发服务器...")
    print("📍 API端点: http://localhost:5000/api/")
    print("🔍 健康检查: http://localhost:5000/health")
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
