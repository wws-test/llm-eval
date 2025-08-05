# 模型管理相关API
from flask import Blueprint, request, current_app
from app.models import AIModel
from app.services.model_service import ModelService
from app.routes.api.common import (
    api_response, api_error, api_auth_required,
    get_current_api_user, validate_json_data, paginate_query
)

bp = Blueprint('models_api', __name__, url_prefix='/models')

@bp.route('', methods=['GET'])
@api_auth_required
def api_get_models():
    """获取模型列表"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 获取查询参数
        include_system = request.args.get('include_system', 'true').lower() == 'true'
        search = request.args.get('search', '').strip()
        
        # 构建查询
        query = AIModel.query
        
        if not include_system:
            # 只显示用户自定义模型
            query = query.filter_by(is_system_model=False, user_id=user.id)
        else:
            # 显示系统模型和用户自定义模型
            query = query.filter(
                (AIModel.is_system_model == True) | 
                (AIModel.user_id == user.id)
            )
        
        # 搜索过滤
        if search:
            query = query.filter(
                AIModel.display_name.contains(search) |
                AIModel.model_identifier.contains(search) |
                AIModel.provider_name.contains(search)
            )
        
        # 排序
        query = query.order_by(AIModel.is_system_model.desc(), AIModel.created_at.desc())
        
        # 分页
        pagination_data = paginate_query(query)
        
        # 序列化模型数据
        models_data = []
        for model in pagination_data['items']:
            model_dict = {
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
                'created_at': model.created_at.isoformat() if model.created_at else None,
                'updated_at': model.updated_at.isoformat() if model.updated_at else None,
                'encrypted_api_key': bool(model.encrypted_api_key)  # 只返回是否设置了密钥
            }
            models_data.append(model_dict)
        
        return api_response(
            success=True,
            data={
                'models': models_data,
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
        current_app.logger.error(f"获取模型列表API错误: {e}")
        return api_error('获取模型列表失败', 500)

@bp.route('', methods=['POST'])
@api_auth_required
@validate_json_data(['display_name', 'model_identifier', 'api_base_url'])
def api_create_model():
    """创建新模型"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        data = request.get_json()
        
        # 验证模型标识符唯一性
        existing_model = AIModel.query.filter_by(
            model_identifier=data['model_identifier'],
            user_id=user.id
        ).first()
        
        if existing_model:
            return api_error('模型标识符已存在', 400)
        
        # 创建模型
        model_data = {
            'display_name': data['display_name'].strip(),
            'model_identifier': data['model_identifier'].strip(),
            'api_base_url': data['api_base_url'].strip(),
            'provider_name': data.get('provider_name', '').strip() or None,
            'model_type': data.get('model_type', 'openai_compatible'),
            'default_temperature': data.get('default_temperature', 0.7),
            'system_prompt': data.get('system_prompt', '').strip() or None,
            'notes': data.get('notes', '').strip() or None,
            'user_id': user.id,
            'is_system_model': False
        }
        
        # 处理API密钥
        api_key = data.get('api_key', '').strip()
        if api_key:
            model_data['api_key'] = api_key
        
        # 使用ModelService创建模型
        model_service = ModelService()
        model = model_service.create_user_model(user, model_data)
        
        current_app.logger.info(f"用户 {user.username} 创建模型: {model.display_name}")
        
        return api_response(
            success=True,
            data={
                'id': model.id,
                'display_name': model.display_name,
                'model_identifier': model.model_identifier,
                'provider_name': model.provider_name,
                'model_type': model.model_type,
                'api_base_url': model.api_base_url,
                'is_system_model': model.is_system_model,
                'is_validated': model.is_validated,
                'created_at': model.created_at.isoformat() if model.created_at else None
            },
            message='模型创建成功',
            status_code=201
        )
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"创建模型API错误: {e}")
        return api_error('创建模型失败', 500)

@bp.route('/<int:model_id>', methods=['GET'])
@api_auth_required
def api_get_model(model_id):
    """获取单个模型详情"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 查找模型（系统模型或用户自己的模型）
        model = AIModel.query.filter(
            AIModel.id == model_id,
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).first()
        
        if not model:
            return api_error('模型未找到', 404)
        
        model_data = {
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
            'created_at': model.created_at.isoformat() if model.created_at else None,
            'updated_at': model.updated_at.isoformat() if model.updated_at else None,
            'encrypted_api_key': bool(model.encrypted_api_key)
        }
        
        return api_response(success=True, data=model_data)

    except Exception as e:
        current_app.logger.error(f"获取模型详情API错误: {e}")
        return api_error('获取模型详情失败', 500)

@bp.route('/<int:model_id>', methods=['PUT'])
@api_auth_required
@validate_json_data(['display_name', 'model_identifier', 'api_base_url'])
def api_update_model(model_id):
    """更新模型"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 查找用户自己的模型（不能修改系统模型）
        model = AIModel.query.filter_by(
            id=model_id,
            user_id=user.id,
            is_system_model=False
        ).first()

        if not model:
            return api_error('模型未找到或无权限修改', 404)

        data = request.get_json()

        # 验证模型标识符唯一性（排除当前模型）
        existing_model = AIModel.query.filter(
            AIModel.model_identifier == data['model_identifier'],
            AIModel.user_id == user.id,
            AIModel.id != model_id
        ).first()

        if existing_model:
            return api_error('模型标识符已存在', 400)

        # 更新模型数据
        update_data = {
            'display_name': data['display_name'].strip(),
            'model_identifier': data['model_identifier'].strip(),
            'api_base_url': data['api_base_url'].strip(),
            'provider_name': data.get('provider_name', '').strip() or None,
            'model_type': data.get('model_type', model.model_type),
            'default_temperature': data.get('default_temperature', model.default_temperature),
            'system_prompt': data.get('system_prompt', '').strip() or None,
            'notes': data.get('notes', '').strip() or None
        }

        # 处理API密钥更新
        api_key = data.get('api_key', '').strip()
        if api_key:
            update_data['api_key'] = api_key

        # 使用ModelService更新模型
        model_service = ModelService()
        updated_model = model_service.update_user_model(model, update_data)

        current_app.logger.info(f"用户 {user.username} 更新模型: {updated_model.display_name}")

        return api_response(
            success=True,
            data={
                'id': updated_model.id,
                'display_name': updated_model.display_name,
                'model_identifier': updated_model.model_identifier,
                'provider_name': updated_model.provider_name,
                'model_type': updated_model.model_type,
                'api_base_url': updated_model.api_base_url,
                'is_validated': updated_model.is_validated,
                'updated_at': updated_model.updated_at.isoformat() if updated_model.updated_at else None
            },
            message='模型更新成功'
        )

    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"更新模型API错误: {e}")
        return api_error('更新模型失败', 500)

@bp.route('/<int:model_id>', methods=['DELETE'])
@api_auth_required
def api_delete_model(model_id):
    """删除模型"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 查找用户自己的模型（不能删除系统模型）
        model = AIModel.query.filter_by(
            id=model_id,
            user_id=user.id,
            is_system_model=False
        ).first()

        if not model:
            return api_error('模型未找到或无权限删除', 404)

        model_name = model.display_name

        # 使用ModelService删除模型
        model_service = ModelService()
        model_service.delete_user_model(model)

        current_app.logger.info(f"用户 {user.username} 删除模型: {model_name}")

        return api_response(
            success=True,
            message=f'模型 "{model_name}" 删除成功'
        )

    except Exception as e:
        current_app.logger.error(f"删除模型API错误: {e}")
        return api_error('删除模型失败', 500)

@bp.route('/<int:model_id>/validate', methods=['POST'])
@api_auth_required
def api_validate_model(model_id):
    """验证模型连通性"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 查找模型（系统模型或用户自己的模型）
        model = AIModel.query.filter(
            AIModel.id == model_id,
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).first()

        if not model:
            return api_error('模型未找到', 404)

        # 使用ModelService验证模型
        model_service = ModelService()
        validation_result = model_service.validate_model(model)

        if validation_result['success']:
            current_app.logger.info(f"模型 {model.display_name} 验证成功")
            return api_response(
                success=True,
                data={
                    'validated': True,
                    'response_time': validation_result.get('response_time'),
                    'model_info': validation_result.get('model_info')
                },
                message='模型验证成功'
            )
        else:
            current_app.logger.warning(f"模型 {model.display_name} 验证失败: {validation_result.get('error')}")
            return api_response(
                success=False,
                data={
                    'validated': False,
                    'error': validation_result.get('error')
                },
                error='模型验证失败'
            )

    except Exception as e:
        current_app.logger.error(f"验证模型API错误: {e}")
        return api_error('验证模型失败', 500)
