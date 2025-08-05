# 评估相关API
from flask import Blueprint, request, current_app
from app.models import ModelEvaluation
from app.routes.api.common import (
    api_response, api_error, api_auth_required, 
    get_current_api_user, validate_json_data, paginate_query
)

bp = Blueprint('eval_api', __name__, url_prefix='/evaluations')

@bp.route('', methods=['GET'])
@api_auth_required
def api_get_evaluations():
    """获取评估列表"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 获取查询参数
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        eval_type = request.args.get('type', '').strip()
        
        # 构建查询 - 只显示用户自己的评估
        query = ModelEvaluation.query.filter_by(user_id=user.id)

        # 搜索过滤
        if search:
            query = query.filter(
                ModelEvaluation.name.contains(search) |
                ModelEvaluation.description.contains(search)
            )

        # 状态过滤
        if status:
            query = query.filter_by(status=status)

        # 类型过滤
        if eval_type:
            query = query.filter_by(evaluation_type=eval_type)

        # 排序
        query = query.order_by(ModelEvaluation.created_at.desc())
        
        # 分页
        pagination_data = paginate_query(query)
        
        # 序列化评估数据
        evaluations_data = []
        for evaluation in pagination_data['items']:
            eval_dict = {
                'id': evaluation.id,
                'name': evaluation.name,
                'description': evaluation.description,
                'evaluation_type': evaluation.evaluation_type,
                'status': evaluation.status,
                'model_id': evaluation.model_id,
                'model_name': evaluation.model.display_name if evaluation.model else None,
                'dataset_id': evaluation.dataset_id,
                'dataset_name': evaluation.dataset.name if evaluation.dataset else None,
                'progress': evaluation.progress,
                'total_samples': evaluation.total_samples,
                'completed_samples': evaluation.completed_samples,
                'created_at': evaluation.created_at.isoformat() if evaluation.created_at else None,
                'updated_at': evaluation.updated_at.isoformat() if evaluation.updated_at else None,
                'completed_at': evaluation.completed_at.isoformat() if evaluation.completed_at else None
            }
            evaluations_data.append(eval_dict)
        
        return api_response(
            success=True,
            data={
                'evaluations': evaluations_data,
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
        current_app.logger.error(f"获取评估列表API错误: {e}")
        return api_error('获取评估列表失败', 500)

@bp.route('', methods=['POST'])
@api_auth_required
@validate_json_data(['name', 'evaluation_type', 'model_id', 'dataset_id'])
def api_create_evaluation():
    """创建新评估"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        data = request.get_json()
        
        # 验证模型权限
        from app.models import AIModel
        model = AIModel.query.filter(
            AIModel.id == data['model_id'],
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).first()
        
        if not model:
            return api_error('模型未找到或无权限使用', 404)
        
        # 验证数据集权限
        from app.models import Dataset
        dataset = Dataset.query.filter_by(
            id=data['dataset_id'],
            user_id=user.id
        ).first()
        
        if not dataset:
            return api_error('数据集未找到', 404)
        
        # 创建评估
        evaluation = ModelEvaluation(
            name=data['name'].strip(),
            description=data.get('description', '').strip() or None,
            evaluation_type=data['evaluation_type'],
            model_id=data['model_id'],
            dataset_id=data['dataset_id'],
            user_id=user.id,
            status='pending',
            progress=0,
            total_samples=dataset.record_count or 0,
            completed_samples=0
        )
        
        from app import db
        db.session.add(evaluation)
        db.session.commit()
        
        current_app.logger.info(f"用户 {user.username} 创建评估: {evaluation.name}")
        
        return api_response(
            success=True,
            data={
                'id': evaluation.id,
                'name': evaluation.name,
                'description': evaluation.description,
                'evaluation_type': evaluation.evaluation_type,
                'status': evaluation.status,
                'model_name': model.display_name,
                'dataset_name': dataset.name,
                'created_at': evaluation.created_at.isoformat() if evaluation.created_at else None
            },
            message='评估创建成功',
            status_code=201
        )
        
    except Exception as e:
        current_app.logger.error(f"创建评估API错误: {e}")
        return api_error('创建评估失败', 500)

@bp.route('/<int:evaluation_id>', methods=['GET'])
@api_auth_required
def api_get_evaluation(evaluation_id):
    """获取单个评估详情"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 查找用户自己的评估
        evaluation = ModelEvaluation.query.filter_by(
            id=evaluation_id,
            user_id=user.id
        ).first()
        
        if not evaluation:
            return api_error('评估未找到', 404)
        
        eval_data = {
            'id': evaluation.id,
            'name': evaluation.name,
            'description': evaluation.description,
            'evaluation_type': evaluation.evaluation_type,
            'status': evaluation.status,
            'model_id': evaluation.model_id,
            'model_name': evaluation.model.display_name if evaluation.model else None,
            'dataset_id': evaluation.dataset_id,
            'dataset_name': evaluation.dataset.name if evaluation.dataset else None,
            'progress': evaluation.progress,
            'total_samples': evaluation.total_samples,
            'completed_samples': evaluation.completed_samples,
            'results': evaluation.results,
            'error_message': evaluation.error_message,
            'created_at': evaluation.created_at.isoformat() if evaluation.created_at else None,
            'updated_at': evaluation.updated_at.isoformat() if evaluation.updated_at else None,
            'completed_at': evaluation.completed_at.isoformat() if evaluation.completed_at else None
        }
        
        return api_response(success=True, data=eval_data)
        
    except Exception as e:
        current_app.logger.error(f"获取评估详情API错误: {e}")
        return api_error('获取评估详情失败', 500)

@bp.route('/<int:evaluation_id>', methods=['DELETE'])
@api_auth_required
def api_delete_evaluation(evaluation_id):
    """删除评估"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 查找用户自己的评估
        evaluation = ModelEvaluation.query.filter_by(
            id=evaluation_id,
            user_id=user.id
        ).first()
        
        if not evaluation:
            return api_error('评估未找到', 404)
        
        # 检查评估状态
        if evaluation.status == 'running':
            return api_error('正在运行的评估无法删除', 400)
        
        eval_name = evaluation.name
        
        # 删除评估
        from app import db
        db.session.delete(evaluation)
        db.session.commit()
        
        current_app.logger.info(f"用户 {user.username} 删除评估: {eval_name}")
        
        return api_response(
            success=True,
            message=f'评估 "{eval_name}" 删除成功'
        )
        
    except Exception as e:
        current_app.logger.error(f"删除评估API错误: {e}")
        return api_error('删除评估失败', 500)

@bp.route('/<int:evaluation_id>/start', methods=['POST'])
@api_auth_required
def api_start_evaluation(evaluation_id):
    """启动评估"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 查找用户自己的评估
        evaluation = ModelEvaluation.query.filter_by(
            id=evaluation_id,
            user_id=user.id
        ).first()
        
        if not evaluation:
            return api_error('评估未找到', 404)
        
        # 检查评估状态
        if evaluation.status != 'pending':
            return api_error('只能启动待执行状态的评估', 400)
        
        # 更新状态为运行中
        evaluation.status = 'running'
        evaluation.progress = 0
        
        from app import db
        db.session.commit()
        
        # 这里应该启动后台任务执行评估
        # 目前只是模拟状态更新
        current_app.logger.info(f"启动评估: {evaluation.name}")
        
        return api_response(
            success=True,
            data={
                'id': evaluation.id,
                'status': evaluation.status,
                'progress': evaluation.progress
            },
            message='评估启动成功'
        )
        
    except Exception as e:
        current_app.logger.error(f"启动评估API错误: {e}")
        return api_error('启动评估失败', 500)

@bp.route('/<int:evaluation_id>/stop', methods=['POST'])
@api_auth_required
def api_stop_evaluation(evaluation_id):
    """停止评估"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 查找用户自己的评估
        evaluation = ModelEvaluation.query.filter_by(
            id=evaluation_id,
            user_id=user.id
        ).first()
        
        if not evaluation:
            return api_error('评估未找到', 404)
        
        # 检查评估状态
        if evaluation.status != 'running':
            return api_error('只能停止运行中的评估', 400)
        
        # 更新状态为已停止
        evaluation.status = 'stopped'
        
        from app import db
        db.session.commit()
        
        current_app.logger.info(f"停止评估: {evaluation.name}")
        
        return api_response(
            success=True,
            data={
                'id': evaluation.id,
                'status': evaluation.status,
                'progress': evaluation.progress
            },
            message='评估停止成功'
        )
        
    except Exception as e:
        current_app.logger.error(f"停止评估API错误: {e}")
        return api_error('停止评估失败', 500)
