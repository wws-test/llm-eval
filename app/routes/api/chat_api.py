# 对话相关API
from flask import Blueprint, request, current_app, Response
from app.models import ChatSession, ChatMessage
from app.routes.api.common import (
    api_response, api_error, api_auth_required, 
    get_current_api_user, validate_json_data, paginate_query
)
import json
import time

bp = Blueprint('chat_api', __name__, url_prefix='/chat')

@bp.route('/sessions', methods=['GET'])
@api_auth_required
def api_get_chat_sessions():
    """获取对话会话列表"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 构建查询 - 只显示用户自己的会话
        query = ChatSession.query.filter_by(user_id=user.id)
        
        # 排序
        query = query.order_by(ChatSession.updated_at.desc())
        
        # 分页
        pagination_data = paginate_query(query)
        
        # 序列化会话数据
        sessions_data = []
        for session in pagination_data['items']:
            # 获取最后一条消息
            last_message = ChatMessage.query.filter_by(
                session_id=session.id
            ).order_by(ChatMessage.created_at.desc()).first()
            
            session_dict = {
                'id': session.id,
                'title': session.title,
                'model_id': session.model_id,
                'model_name': session.model.display_name if session.model else None,
                'message_count': session.messages.count(),
                'last_message': last_message.content[:100] + '...' if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'updated_at': session.updated_at.isoformat() if session.updated_at else None
            }
            sessions_data.append(session_dict)
        
        return api_response(
            success=True,
            data={
                'sessions': sessions_data,
                'pagination': {
                    'total': pagination_data['total'],
                    'page': pagination_data['page'],
                    'per_page': pagination_data['per_page'],
                    'pages': pagination_data['pages'],
                    'has_next': pagination_data['has_next'],
                    'has_prev': pagination_data['has_prev']
                }
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"获取对话会话列表API错误: {e}")
        return api_error('获取对话会话列表失败', 500)

@bp.route('/sessions', methods=['POST'])
@api_auth_required
@validate_json_data(['model_id'])
def api_create_chat_session():
    """创建新的对话会话"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        data = request.get_json()
        model_id = data['model_id']
        
        # 验证模型是否存在且用户有权限使用
        from app.models import AIModel
        model = AIModel.query.filter(
            AIModel.id == model_id,
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).first()
        
        if not model:
            return api_error('模型未找到或无权限使用', 404)
        
        # 创建会话
        session = ChatSession(
            title=data.get('title', '新的对话'),
            model_id=model_id,
            user_id=user.id
        )
        
        from app import db
        db.session.add(session)
        db.session.commit()
        
        current_app.logger.info(f"用户 {user.username} 创建对话会话: {session.title}")
        
        return api_response(
            success=True,
            data={
                'id': session.id,
                'title': session.title,
                'model_id': session.model_id,
                'model_name': model.display_name,
                'created_at': session.created_at.isoformat() if session.created_at else None
            },
            message='对话会话创建成功',
            status_code=201
        )
        
    except Exception as e:
        current_app.logger.error(f"创建对话会话API错误: {e}")
        return api_error('创建对话会话失败', 500)

@bp.route('/sessions/<int:session_id>', methods=['GET'])
@api_auth_required
def api_get_chat_session(session_id):
    """获取对话会话详情和消息历史"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 查找用户自己的会话
        session = ChatSession.query.filter_by(
            id=session_id,
            user_id=user.id
        ).first()
        
        if not session:
            return api_error('对话会话未找到', 404)
        
        # 获取消息历史
        messages = ChatMessage.query.filter_by(
            session_id=session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        messages_data = []
        for message in messages:
            message_dict = {
                'id': message.id,
                'role': message.role,
                'content': message.content,
                'created_at': message.created_at.isoformat() if message.created_at else None
            }
            messages_data.append(message_dict)
        
        session_data = {
            'id': session.id,
            'title': session.title,
            'model_id': session.model_id,
            'model_name': session.model.display_name if session.model else None,
            'messages': messages_data,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'updated_at': session.updated_at.isoformat() if session.updated_at else None
        }
        
        return api_response(success=True, data=session_data)
        
    except Exception as e:
        current_app.logger.error(f"获取对话会话详情API错误: {e}")
        return api_error('获取对话会话详情失败', 500)

@bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@api_auth_required
def api_delete_chat_session(session_id):
    """删除对话会话"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 查找用户自己的会话
        session = ChatSession.query.filter_by(
            id=session_id,
            user_id=user.id
        ).first()
        
        if not session:
            return api_error('对话会话未找到', 404)
        
        session_title = session.title
        
        # 删除会话（级联删除消息）
        from app import db
        db.session.delete(session)
        db.session.commit()
        
        current_app.logger.info(f"用户 {user.username} 删除对话会话: {session_title}")
        
        return api_response(
            success=True,
            message=f'对话会话 "{session_title}" 删除成功'
        )
        
    except Exception as e:
        current_app.logger.error(f"删除对话会话API错误: {e}")
        return api_error('删除对话会话失败', 500)

@bp.route('/completions', methods=['POST'])
@api_auth_required
@validate_json_data(['session_id', 'message'])
def api_chat_completion():
    """发送消息并获取AI回复"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        data = request.get_json()
        session_id = data['session_id']
        user_message = data['message'].strip()
        
        if not user_message:
            return api_error('消息内容不能为空', 400)
        
        # 验证会话
        session = ChatSession.query.filter_by(
            id=session_id,
            user_id=user.id
        ).first()
        
        if not session:
            return api_error('对话会话未找到', 404)
        
        # 保存用户消息
        user_msg = ChatMessage(
            session_id=session_id,
            role='user',
            content=user_message
        )
        
        from app import db
        db.session.add(user_msg)
        db.session.commit()
        
        # 更新会话标题（如果是第一条消息）
        if session.messages.count() == 1:
            session.title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            db.session.commit()
        
        # 模拟AI回复（实际应用中这里会调用AI模型）
        ai_response = f"这是对 '{user_message}' 的模拟回复。实际应用中这里会调用AI模型API。"
        
        # 保存AI回复
        ai_msg = ChatMessage(
            session_id=session_id,
            role='assistant',
            content=ai_response
        )
        
        db.session.add(ai_msg)
        session.updated_at = db.func.now()
        db.session.commit()
        
        return api_response(
            success=True,
            data={
                'user_message': {
                    'id': user_msg.id,
                    'role': 'user',
                    'content': user_message,
                    'created_at': user_msg.created_at.isoformat()
                },
                'ai_message': {
                    'id': ai_msg.id,
                    'role': 'assistant',
                    'content': ai_response,
                    'created_at': ai_msg.created_at.isoformat()
                }
            },
            message='消息发送成功'
        )
        
    except Exception as e:
        current_app.logger.error(f"对话完成API错误: {e}")
        return api_error('发送消息失败', 500)
