# 统计数据相关API
from flask import Blueprint, current_app
from app.models import AIModel, ChatSession, Dataset, ModelEvaluation, RAGEvaluation, PerformanceEvalTask
from app.routes.api.common import (
    api_response, api_error, api_auth_required, get_current_api_user
)
from app import db

bp = Blueprint('stats_api', __name__, url_prefix='/stats')

@bp.route('/dashboard', methods=['GET'])
@api_auth_required
def api_get_dashboard_stats():
    """获取仪表盘统计数据"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 统计模型数量
        total_models = AIModel.query.filter(
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).count()
        
        user_models = AIModel.query.filter_by(
            user_id=user.id, 
            is_system_model=False
        ).count()
        
        system_models = AIModel.query.filter_by(is_system_model=True).count()
        
        # 统计对话数量
        total_chats = ChatSession.query.filter_by(user_id=user.id).count()
        
        # 统计数据集数量
        total_datasets = Dataset.query.count()  # 内部项目，显示所有数据集
        
        # 统计评估任务数量
        model_evaluations = ModelEvaluation.query.filter_by(user_id=user.id).count()
        rag_evaluations = RAGEvaluation.query.filter_by(user_id=user.id).count()
        perf_evaluations = PerformanceEvalTask.query.filter_by(user_id=user.id).count()
        total_evaluations = model_evaluations + rag_evaluations + perf_evaluations
        
        # 最近活动统计
        recent_chats = ChatSession.query.filter_by(user_id=user.id)\
            .order_by(ChatSession.updated_at.desc()).limit(5).all()
        
        recent_evaluations = []
        
        # 获取最近的模型评估
        recent_model_evals = ModelEvaluation.query.filter_by(user_id=user.id)\
            .order_by(ModelEvaluation.created_at.desc()).limit(3).all()
        for eval_task in recent_model_evals:
            recent_evaluations.append({
                'id': eval_task.id,
                'type': 'model_evaluation',
                'name': f"模型评估 #{eval_task.id}",
                'status': eval_task.status,
                'created_at': eval_task.created_at.isoformat() if eval_task.created_at else None
            })
        
        # 获取最近的RAG评估
        recent_rag_evals = RAGEvaluation.query.filter_by(user_id=user.id)\
            .order_by(RAGEvaluation.created_at.desc()).limit(2).all()
        for eval_task in recent_rag_evals:
            recent_evaluations.append({
                'id': eval_task.id,
                'type': 'rag_evaluation',
                'name': f"RAG评估 #{eval_task.id}",
                'status': eval_task.status,
                'created_at': eval_task.created_at.isoformat() if eval_task.created_at else None
            })
        
        # 按时间排序最近评估
        recent_evaluations.sort(key=lambda x: x['created_at'] or '', reverse=True)
        recent_evaluations = recent_evaluations[:5]
        
        # 模型验证状态统计
        validated_models = AIModel.query.filter(
            AIModel.is_validated == True,
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).count()
        
        unvalidated_models = total_models - validated_models
        
        stats_data = {
            'overview': {
                'total_models': total_models,
                'total_chats': total_chats,
                'total_datasets': total_datasets,
                'total_evaluations': total_evaluations
            },
            'models': {
                'total': total_models,
                'user_models': user_models,
                'system_models': system_models,
                'validated': validated_models,
                'unvalidated': unvalidated_models
            },
            'evaluations': {
                'total': total_evaluations,
                'model_evaluations': model_evaluations,
                'rag_evaluations': rag_evaluations,
                'performance_evaluations': perf_evaluations
            },
            'recent_activity': {
                'recent_chats': [
                    {
                        'id': chat.id,
                        'title': chat.title,
                        'updated_at': chat.updated_at.isoformat() if chat.updated_at else None
                    } for chat in recent_chats
                ],
                'recent_evaluations': recent_evaluations
            }
        }
        
        return api_response(
            success=True,
            data=stats_data,
            message='统计数据获取成功'
        )
        
    except Exception as e:
        current_app.logger.error(f"获取统计数据API错误: {e}")
        return api_error('获取统计数据失败', 500)

@bp.route('/models', methods=['GET'])
@api_auth_required
def api_get_model_stats():
    """获取模型相关统计数据"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 按模型类型统计
        model_types = db.session.query(
            AIModel.model_type, 
            db.func.count(AIModel.id).label('count')
        ).filter(
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).group_by(AIModel.model_type).all()
        
        # 按提供商统计
        providers = db.session.query(
            AIModel.provider_name, 
            db.func.count(AIModel.id).label('count')
        ).filter(
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id),
            AIModel.provider_name.isnot(None)
        ).group_by(AIModel.provider_name).all()
        
        stats_data = {
            'by_type': [
                {'type': model_type, 'count': count} 
                for model_type, count in model_types
            ],
            'by_provider': [
                {'provider': provider or '未知', 'count': count} 
                for provider, count in providers
            ]
        }
        
        return api_response(
            success=True,
            data=stats_data,
            message='模型统计数据获取成功'
        )
        
    except Exception as e:
        current_app.logger.error(f"获取模型统计数据API错误: {e}")
        return api_error('获取模型统计数据失败', 500)
