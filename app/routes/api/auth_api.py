# 认证相关API
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash
from app.models import User
from app.routes.api.common import (
    api_response, api_error, generate_simple_token, 
    api_auth_required, get_current_api_user, validate_json_data
)

bp = Blueprint('auth_api', __name__, url_prefix='/auth')

@bp.route('/login', methods=['POST'])
@validate_json_data(['username', 'password'])
def api_login():
    """API登录端点"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return api_error('用户名和密码不能为空', 400)
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # 如果用户不存在，创建新用户（首次登录逻辑）
            current_app.logger.info(f"创建新用户: {username}")
            user = User(username=username)
            user.set_password(password)  # 使用输入的密码作为初始密码
            
            from app import db
            db.session.add(user)
            db.session.commit()
            
            # 生成token
            token = generate_simple_token(user.id, user.username)
            
            return api_response(
                success=True,
                data={
                    'token': token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'created_at': user.created_at.isoformat() if user.created_at else None
                    },
                    'is_new_user': True
                },
                message='账户创建成功，请及时修改密码'
            )
        else:
            # 验证现有用户密码
            if user.check_password(password):
                # 生成token
                token = generate_simple_token(user.id, user.username)
                
                return api_response(
                    success=True,
                    data={
                        'token': token,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'created_at': user.created_at.isoformat() if user.created_at else None
                        },
                        'is_new_user': False
                    },
                    message='登录成功'
                )
            else:
                return api_error('用户名或密码错误', 401)
                
    except Exception as e:
        current_app.logger.error(f"登录API错误: {e}")
        return api_error('登录失败，请重试', 500)

@bp.route('/logout', methods=['POST'])
@api_auth_required
def api_logout():
    """API登出端点"""
    try:
        # 在简单token实现中，登出主要是客户端删除token
        # 这里可以记录登出日志或进行其他清理工作
        user = get_current_api_user()
        if user:
            current_app.logger.info(f"用户 {user.username} 登出")
            
        return api_response(
            success=True,
            message='登出成功'
        )
    except Exception as e:
        current_app.logger.error(f"登出API错误: {e}")
        return api_error('登出失败', 500)

@bp.route('/me', methods=['GET'])
@api_auth_required
def api_get_current_user():
    """获取当前用户信息"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户不存在', 404)
            
        return api_response(
            success=True,
            data={
                'id': user.id,
                'username': user.username,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        )
    except Exception as e:
        current_app.logger.error(f"获取用户信息API错误: {e}")
        return api_error('获取用户信息失败', 500)

@bp.route('/change-password', methods=['POST'])
@api_auth_required
@validate_json_data(['current_password', 'new_password'])
def api_change_password():
    """修改密码"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户不存在', 404)
            
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        # 验证当前密码
        if not user.check_password(current_password):
            return api_error('当前密码错误', 400)
            
        # 验证新密码强度（简单验证）
        if len(new_password) < 6:
            return api_error('新密码长度至少6位', 400)
            
        # 更新密码
        user.set_password(new_password)
        from app import db
        db.session.commit()
        
        current_app.logger.info(f"用户 {user.username} 修改密码成功")
        
        return api_response(
            success=True,
            message='密码修改成功'
        )
        
    except Exception as e:
        current_app.logger.error(f"修改密码API错误: {e}")
        return api_error('修改密码失败', 500)

@bp.route('/verify-token', methods=['POST'])
@api_auth_required
def api_verify_token():
    """验证token有效性"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('Token无效', 401)
            
        return api_response(
            success=True,
            data={
                'valid': True,
                'user': {
                    'id': user.id,
                    'username': user.username
                }
            }
        )
    except Exception as e:
        current_app.logger.error(f"验证token API错误: {e}")
        return api_error('Token验证失败', 500)
