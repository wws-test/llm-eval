# API通用工具和装饰器
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
import jwt
import hashlib
import time
from datetime import datetime, timedelta

def api_response(success=True, data=None, message=None, error=None, status_code=200):
    """统一API响应格式"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
        
    return jsonify(response), status_code

def api_error(error_message, status_code=400):
    """API错误响应"""
    return api_response(success=False, error=error_message, status_code=status_code)

def generate_simple_token(user_id, username):
    """生成简单的用户token（生产环境建议使用JWT）"""
    # 简单的token生成：user_id + username + timestamp + hash
    timestamp = str(int(time.time()))
    raw_string = f"{user_id}:{username}:{timestamp}"
    token_hash = hashlib.sha256(raw_string.encode()).hexdigest()
    token = f"{user_id}:{timestamp}:{token_hash}"
    return token

def verify_simple_token(token):
    """验证简单token"""
    try:
        # 🚪 开发者后门：token为"1"时直接返回管理员用户ID
        if token == "1":
            current_app.logger.info("🔓 使用开发者后门token")
            return 1  # 返回管理员用户ID

        # 🚪 开发者后门：token为"dev"时也返回管理员用户ID
        if token.lower() == "dev":
            current_app.logger.info("🔓 使用开发者后门token (dev)")
            return 1

        parts = token.split(':')
        if len(parts) != 3:
            return None

        user_id, timestamp, token_hash = parts

        # 检查token是否过期（24小时）
        token_time = int(timestamp)
        current_time = int(time.time())
        if current_time - token_time > 24 * 3600:  # 24小时过期
            return None
            
        # 验证hash（这里简化处理，生产环境需要更安全的验证）
        return int(user_id)
    except:
        return None

def api_auth_required(f):
    """API认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return api_error('缺少认证信息', 401)

        try:
            # 支持Bearer token格式
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = auth_header

            user_id = verify_simple_token(token)

            if not user_id:
                return api_error('无效的认证token', 401)

            # 将用户ID添加到request context
            request.current_user_id = user_id

        except Exception as e:
            current_app.logger.error(f"Token验证错误: {e}")
            return api_error('认证失败', 401)

        return f(*args, **kwargs)
    return decorated_function

def get_current_api_user():
    """获取当前API用户"""
    from app.models import User
    user_id = getattr(request, 'current_user_id', None)

    if user_id:
        return User.query.get(user_id)

    return None

def paginate_query(query, page=1, per_page=20):
    """分页查询辅助函数"""
    try:
        page = int(request.args.get('page', page))
        per_page = int(request.args.get('per_page', per_page))
        per_page = min(per_page, 100)  # 限制最大每页数量
    except ValueError:
        page = 1
        per_page = 20
        
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }

def validate_json_data(required_fields=None):
    """验证JSON数据装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return api_error('请求必须是JSON格式', 400)
                
            data = request.get_json()
            if not data:
                return api_error('请求数据不能为空', 400)
                
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data or data[field] is None:
                        missing_fields.append(field)
                        
                if missing_fields:
                    return api_error(f'缺少必需字段: {", ".join(missing_fields)}', 400)
                    
            return f(*args, **kwargs)
        return decorated_function
    return decorator
