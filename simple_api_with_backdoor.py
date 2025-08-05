#!/usr/bin/env python3
"""
带开发者后门的简化API服务器
支持token="1"或"dev"直接访问所有API
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import hashlib
import time

# 创建Flask应用
app = Flask(__name__)

# 基础配置
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///simple_llm_eval.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db = SQLAlchemy(app)
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'])

# 简化的模型定义
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AIModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(100), nullable=False)
    model_identifier = db.Column(db.String(100), nullable=False)
    provider_name = db.Column(db.String(50))
    model_type = db.Column(db.String(50), default='openai_compatible')
    api_base_url = db.Column(db.String(200), nullable=False)
    is_system_model = db.Column(db.Boolean, default=False)
    is_validated = db.Column(db.Boolean, default=False)
    default_temperature = db.Column(db.Float, default=0.7)
    system_prompt = db.Column(db.Text)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default='新的对话')
    model_id = db.Column(db.Integer, db.ForeignKey('ai_model.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 关系
    model = db.relationship('AIModel', backref='chat_sessions')
    user = db.relationship('User', backref='chat_sessions')
    messages = db.relationship('ChatMessage', backref='session', cascade='all, delete-orphan')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# 工具函数
def generate_token(user_id, username):
    timestamp = str(int(time.time()))
    raw_string = f"{user_id}:{username}:{timestamp}"
    token_hash = hashlib.sha256(raw_string.encode()).hexdigest()
    return f"{user_id}:{timestamp}:{token_hash}"

def verify_token(token):
    """验证token，支持开发者后门"""
    try:
        # 🚪 开发者后门：token为"1"时直接返回管理员用户ID
        if token == "1":
            print("🔓 使用开发者后门token: 1")
            return 1
        
        # 🚪 开发者后门：token为"dev"时也返回管理员用户ID  
        if token.lower() == "dev":
            print("🔓 使用开发者后门token: dev")
            return 1
            
        # 正常token验证
        parts = token.split(':')
        if len(parts) != 3:
            return None
        user_id, timestamp, token_hash = parts
        token_time = int(timestamp)
        current_time = int(time.time())
        if current_time - token_time > 24 * 3600:  # 24小时过期
            return None
        return int(user_id)
    except:
        return None

def api_response(success=True, data=None, message=None, error=None, status_code=200):
    response = {
        'success': success,
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
    return jsonify(response), status_code

def require_auth(f):
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return api_response(False, error='缺少认证信息', status_code=401)
        
        # 支持Bearer token格式
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            token = auth_header
            
        user_id = verify_token(token)
        if not user_id:
            return api_response(False, error='无效的认证token', status_code=401)
        
        request.current_user_id = user_id
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# API路由
@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'API服务运行正常'}

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return api_response(False, error='用户名和密码不能为空', status_code=400)
    
    username = data['username'].strip()
    password = data['password']
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        # 创建新用户
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        token = generate_token(user.id, user.username)
        return api_response(True, {
            'token': token,
            'user': {'id': user.id, 'username': user.username},
            'is_new_user': True
        }, '账户创建成功')
    else:
        if user.check_password(password):
            token = generate_token(user.id, user.username)
            return api_response(True, {
                'token': token,
                'user': {'id': user.id, 'username': user.username},
                'is_new_user': False
            }, '登录成功')
        else:
            return api_response(False, error='用户名或密码错误', status_code=401)

@app.route('/api/models', methods=['GET'])
@require_auth
def get_models():
    user_id = request.current_user_id
    
    # 获取系统模型和用户自定义模型
    models = AIModel.query.filter(
        (AIModel.is_system_model == True) | (AIModel.user_id == user_id)
    ).order_by(AIModel.is_system_model.desc(), AIModel.created_at.desc()).all()
    
    models_data = []
    for model in models:
        models_data.append({
            'id': model.id,
            'display_name': model.display_name,
            'model_identifier': model.model_identifier,
            'provider_name': model.provider_name,
            'model_type': model.model_type,
            'api_base_url': model.api_base_url,
            'is_system_model': model.is_system_model,
            'is_validated': model.is_validated,
            'default_temperature': model.default_temperature,
            'system_prompt': model.system_prompt,
            'notes': model.notes,
            'created_at': model.created_at.isoformat() if model.created_at else None
        })
    
    return api_response(True, {
        'models': models_data,
        'pagination': {'total': len(models_data)}
    })

@app.route('/api/models', methods=['POST'])
@require_auth
def create_model():
    user_id = request.current_user_id
    data = request.get_json()
    
    if not data or not all(k in data for k in ['display_name', 'model_identifier', 'api_base_url']):
        return api_response(False, error='缺少必需字段', status_code=400)
    
    # 检查模型标识符唯一性
    existing = AIModel.query.filter_by(
        model_identifier=data['model_identifier'],
        user_id=user_id
    ).first()
    
    if existing:
        return api_response(False, error='模型标识符已存在', status_code=400)
    
    model = AIModel(
        display_name=data['display_name'],
        model_identifier=data['model_identifier'],
        api_base_url=data['api_base_url'],
        provider_name=data.get('provider_name'),
        default_temperature=data.get('default_temperature', 0.7),
        system_prompt=data.get('system_prompt'),
        notes=data.get('notes'),
        user_id=user_id,
        is_system_model=False
    )
    
    db.session.add(model)
    db.session.commit()
    
    return api_response(True, {
        'id': model.id,
        'display_name': model.display_name,
        'model_identifier': model.model_identifier
    }, '模型创建成功', status_code=201)

@app.route('/api/models/<int:model_id>/validate', methods=['POST'])
@require_auth
def validate_model(model_id):
    user_id = request.current_user_id
    
    model = AIModel.query.filter(
        AIModel.id == model_id,
        (AIModel.is_system_model == True) | (AIModel.user_id == user_id)
    ).first()
    
    if not model:
        return api_response(False, error='模型未找到', status_code=404)
    
    # 模拟验证过程
    import time
    time.sleep(1)  # 模拟验证延迟
    
    # 更新验证状态
    model.is_validated = True
    db.session.commit()
    
    return api_response(True, {
        'validated': True,
        'response_time': 1.0
    }, '模型验证成功')

@app.route('/api/dev/info', methods=['GET'])
@require_auth
def dev_info():
    """开发者信息接口，显示当前用户和后门状态"""
    user_id = request.current_user_id
    user = User.query.get(user_id)
    
    # 检查是否使用了后门
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else auth_header
    is_backdoor = token in ['1', 'dev']
    
    return api_response(True, {
        'current_user': {
            'id': user.id,
            'username': user.username
        } if user else None,
        'is_backdoor_access': is_backdoor,
        'token_used': token[:10] + '...' if len(token) > 10 else token,
        'total_users': User.query.count(),
        'total_models': AIModel.query.count()
    })

# 聊天相关API
@app.route('/api/chat/sessions', methods=['GET'])
@require_auth
def get_chat_sessions():
    """获取对话会话列表"""
    user_id = request.current_user_id

    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()

    sessions_data = []
    for session in sessions:
        # 获取消息数量
        message_count = ChatMessage.query.filter_by(session_id=session.id).count()

        sessions_data.append({
            'id': session.id,
            'title': session.title,
            'model_id': session.model_id,
            'model_name': session.model.display_name if session.model else None,
            'message_count': message_count,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'updated_at': session.updated_at.isoformat() if session.updated_at else None
        })

    return api_response(True, {'sessions': sessions_data})

@app.route('/api/chat/sessions', methods=['POST'])
@require_auth
def create_chat_session():
    """创建新的对话会话"""
    user_id = request.current_user_id
    data = request.get_json()

    if not data or 'model_id' not in data:
        return api_response(False, error='缺少必需字段 model_id', status_code=400)

    model_id = data['model_id']

    # 验证模型是否存在
    model = AIModel.query.filter(
        AIModel.id == model_id,
        (AIModel.is_system_model == True) | (AIModel.user_id == user_id)
    ).first()

    if not model:
        return api_response(False, error='模型未找到或无权限使用', status_code=404)

    session = ChatSession(
        title=data.get('title', '新的对话'),
        model_id=model_id,
        user_id=user_id
    )

    db.session.add(session)
    db.session.commit()

    return api_response(True, {
        'id': session.id,
        'title': session.title,
        'model_id': session.model_id,
        'model_name': model.display_name
    }, '对话创建成功', status_code=201)

@app.route('/api/chat/sessions/<int:session_id>/messages', methods=['GET'])
@require_auth
def get_chat_messages(session_id):
    """获取对话消息列表"""
    user_id = request.current_user_id

    # 验证会话权限
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return api_response(False, error='对话会话未找到', status_code=404)

    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()

    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat() if message.created_at else None
        })

    return api_response(True, {'messages': messages_data})

@app.route('/api/chat/sessions/<int:session_id>/send', methods=['POST'])
@require_auth
def send_chat_message(session_id):
    """发送消息并获取AI回复"""
    user_id = request.current_user_id
    data = request.get_json()

    if not data or 'content' not in data:
        return api_response(False, error='缺少消息内容', status_code=400)

    content = data['content'].strip()
    if not content:
        return api_response(False, error='消息内容不能为空', status_code=400)

    # 验证会话权限
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return api_response(False, error='对话会话未找到', status_code=404)

    # 保存用户消息
    user_message = ChatMessage(
        session_id=session_id,
        role='user',
        content=content
    )
    db.session.add(user_message)

    # 模拟AI回复
    ai_response = f"这是对 '{content[:50]}...' 的模拟回复。当前时间: {datetime.datetime.now().strftime('%H:%M:%S')}"

    assistant_message = ChatMessage(
        session_id=session_id,
        role='assistant',
        content=ai_response
    )
    db.session.add(assistant_message)

    # 更新会话时间
    session.updated_at = datetime.datetime.utcnow()

    db.session.commit()

    return api_response(True, {
        'id': assistant_message.id,
        'content': ai_response,
        'created_at': assistant_message.created_at.isoformat()
    }, '消息发送成功')

@app.route('/api/chat/sessions/<int:session_id>/clear', methods=['POST'])
@require_auth
def clear_chat_session(session_id):
    """清空对话会话的所有消息"""
    user_id = request.current_user_id

    # 验证会话权限
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return api_response(False, error='对话会话未找到', status_code=404)

    # 删除所有消息
    ChatMessage.query.filter_by(session_id=session_id).delete()
    db.session.commit()

    return api_response(True, message='对话已清空')

@app.route('/api/chat/sessions/<int:session_id>', methods=['DELETE'])
@require_auth
def delete_chat_session(session_id):
    """删除对话会话"""
    user_id = request.current_user_id

    # 验证会话权限
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return api_response(False, error='对话会话未找到', status_code=404)

    session_title = session.title

    # 删除会话（级联删除消息）
    db.session.delete(session)
    db.session.commit()

    return api_response(True, message=f'对话会话 "{session_title}" 删除成功')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 初始化数据
        if User.query.count() == 0:
            admin = User(username='admin')
            admin.set_password('admin')
            db.session.add(admin)
            
            # 系统模型
            models = [
                AIModel(
                    display_name='GPT-4o',
                    model_identifier='gpt-4o',
                    provider_name='OpenAI',
                    api_base_url='https://api.openai.com/v1',
                    is_system_model=True,
                    is_validated=True
                ),
                AIModel(
                    display_name='Claude-3 Opus',
                    model_identifier='claude-3-opus-20240229',
                    provider_name='Anthropic',
                    api_base_url='https://api.anthropic.com/v1',
                    is_system_model=True,
                    is_validated=True
                )
            ]
            
            for model in models:
                db.session.add(model)
            
            db.session.commit()
            print("✅ 数据库初始化完成")
    
    print("🚀 启动带开发者后门的API服务器...")
    print("📍 API端点: http://localhost:5000/api/")
    print("🔍 健康检查: http://localhost:5000/health")
    print("🚪 开发者后门:")
    print("   - Authorization: Bearer 1")
    print("   - Authorization: Bearer dev")
    print("   - 开发者信息: GET /api/dev/info")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
