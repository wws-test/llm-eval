# 性能评估相关API
from flask import Blueprint, request, current_app
from app.models import PerformanceEvalTask, AIModel, Dataset
from app.routes.api.common import (
    api_response, api_error, api_auth_required, get_current_api_user, validate_json_data
)
from app.services.perf_service import PerformanceEvaluationService, BatchPerformanceEvaluationService
from app import db
from app.utils import get_beijing_time
from sqlalchemy import and_, or_

bp = Blueprint('performance_api', __name__, url_prefix='/performance-eval')

@bp.route('/tasks', methods=['GET'])
@api_auth_required
def api_get_performance_tasks():
    """获取性能评估任务列表"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 获取查询参数
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取任务列表
        tasks, total = PerformanceEvaluationService.get_all_tasks(
            user_id=user.id, 
            page=page, 
            per_page=per_page,
            search=search,
            status=status
        )
        
        # 转换为API格式
        task_list = []
        for task in tasks:
            task_dict = {
                'id': task.id,
                'model_name': task.model_name,
                'dataset_name': task.dataset_name,
                'concurrency': task.concurrency,
                'num_requests': task.num_requests,
                'status': task.status,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            }
            task_list.append(task_dict)
        
        # 计算分页信息
        pages = (total + per_page - 1) // per_page
        
        return api_response(
            success=True,
            data={
                'tasks': task_list,
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': pages,
                    'has_next': page < pages,
                    'has_prev': page > 1
                }
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"获取性能评估任务列表API错误: {e}")
        return api_error('获取任务列表失败', 500)

@bp.route('/tasks/<int:task_id>', methods=['GET'])
@api_auth_required
def api_get_performance_task(task_id):
    """获取性能评估任务详情"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        task = PerformanceEvaluationService.get_task_by_id(task_id, user_id=user.id)
        if not task:
            return api_error('任务不存在或无权限访问', 404)
        
        task_dict = {
            'id': task.id,
            'model_name': task.model_name,
            'dataset_name': task.dataset_name,
            'concurrency': task.concurrency,
            'num_requests': task.num_requests,
            'status': task.status,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'results': task.results if hasattr(task, 'results') else None
        }
        
        return api_response(success=True, data=task_dict)
        
    except Exception as e:
        current_app.logger.error(f"获取性能评估任务详情API错误: {e}")
        return api_error('获取任务详情失败', 500)

@bp.route('/tasks', methods=['POST'])
@api_auth_required
@validate_json_data(['model_id', 'dataset_id', 'concurrency', 'num_requests'])
def api_create_performance_task():
    """创建性能评估任务"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        data = request.get_json()
        
        # 验证模型权限
        model = AIModel.query.filter(
            AIModel.id == data['model_id'],
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).first()
        
        if not model:
            return api_error('模型未找到或无权限使用', 404)
        
        # 验证数据集权限（-1表示使用内置openqa数据集）
        if data['dataset_id'] != -1:
            dataset = Dataset.query.filter(
                Dataset.id == data['dataset_id'],
                and_(
                    Dataset.is_active == True,
                    Dataset.dataset_type == '自建',
                    or_(
                        # 自己创建的自建数据集（无论是否公开）
                        Dataset.source == user.username,
                        # 别人创建的公开自建数据集
                        and_(
                            Dataset.source != user.username,
                            Dataset.visibility == '公开'
                        )
                    ),
                    Dataset.format != 'RAG'
                )
            ).first()
            
            if not dataset:
                return api_error('数据集未找到或无权限使用', 404)
        
        # 创建性能评估任务
        task = PerformanceEvaluationService.create_performance_eval_task(
            model_id=data['model_id'],
            dataset_id=data['dataset_id'],
            concurrency=data['concurrency'],
            num_requests=data['num_requests'],
            user_id=user.id
        )
        
        if not task:
            return api_error('创建性能评估任务失败', 500)
        
        # 启动评估任务
        try:
            PerformanceEvaluationService.run_performance_evaluation(
                task.id,
                data['model_id'],
                data['dataset_id'],
                data['concurrency'],
                data['num_requests'],
                min_prompt_length=data.get('min_prompt_length'),
                max_prompt_length=data.get('max_prompt_length'),
                max_tokens=data.get('max_tokens'),
                extra_args=data.get('extra_args')
            )
        except Exception as e:
            current_app.logger.error(f"启动性能评估任务失败: {e}")
            # 如果启动失败，更新任务状态
            task.status = 'failed'
            db.session.commit()
            return api_error(f'启动性能评估任务失败: {str(e)}', 500)
        
        task_dict = {
            'id': task.id,
            'model_name': task.model_name,
            'dataset_name': task.dataset_name,
            'concurrency': task.concurrency,
            'num_requests': task.num_requests,
            'status': task.status,
            'created_at': task.created_at.isoformat() if task.created_at else None
        }
        
        return api_response(
            success=True,
            data=task_dict,
            message='性能评估任务创建成功'
        )
        
    except Exception as e:
        current_app.logger.error(f"创建性能评估任务API错误: {e}")
        return api_error('创建任务失败', 500)

@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@api_auth_required
def api_delete_performance_task(task_id):
    """删除性能评估任务"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        success = PerformanceEvaluationService.delete_task(task_id, user_id=user.id)
        
        if success:
            return api_response(success=True, message='任务删除成功')
        else:
            return api_error('任务删除失败或任务不存在', 404)
        
    except Exception as e:
        current_app.logger.error(f"删除性能评估任务API错误: {e}")
        return api_error('删除任务失败', 500)

@bp.route('/tasks/recent', methods=['GET'])
@api_auth_required
def api_get_recent_performance_tasks():
    """获取最近的性能评估任务"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        limit = request.args.get('limit', 5, type=int)
        
        # 获取最近的任务
        tasks, _ = PerformanceEvaluationService.get_all_tasks(
            user_id=user.id, 
            page=1, 
            per_page=limit
        )
        
        task_list = []
        for task in tasks:
            task_dict = {
                'id': task.id,
                'model_name': task.model_name,
                'dataset_name': task.dataset_name,
                'status': task.status,
                'created_at': task.created_at.isoformat() if task.created_at else None
            }
            task_list.append(task_dict)
        
        return api_response(success=True, data=task_list)
        
    except Exception as e:
        current_app.logger.error(f"获取最近性能评估任务API错误: {e}")
        return api_error('获取最近任务失败', 500)

@bp.route('/models', methods=['GET'])
@api_auth_required
def api_get_available_models():
    """获取可用的模型列表（用于性能评估）"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)
        
        # 获取用户可用的模型（用户自己的模型 + 系统模型）
        models = AIModel.query.filter(
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).all()
        
        model_list = []
        for model in models:
            model_dict = {
                'id': model.id,
                'name': model.model_identifier,
                'display_name': model.display_name
            }
            model_list.append(model_dict)
        
        return api_response(success=True, data=model_list)
        
    except Exception as e:
        current_app.logger.error(f"获取可用模型列表API错误: {e}")
        return api_error('获取模型列表失败', 500)

@bp.route('/datasets', methods=['GET'])
@api_auth_required
def api_get_available_datasets():
    """获取可用的数据集列表（用于性能评估）"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 获取可用的数据集
        datasets = Dataset.query.filter(
            and_(
                Dataset.is_active == True,
                Dataset.dataset_type == '自建',
                or_(
                    # 自己创建的自建数据集（无论是否公开）
                    Dataset.source == user.username,
                    # 别人创建的公开自建数据集
                    and_(
                        Dataset.source != user.username,
                        Dataset.visibility == '公开'
                    )
                ),
                Dataset.format != 'RAG'
            )
        ).order_by(Dataset.id.desc()).all()

        dataset_list = [
            {'id': -1, 'name': 'openqa', 'description': '内置问答数据集'}
        ]

        for dataset in datasets:
            dataset_dict = {
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description
            }
            dataset_list.append(dataset_dict)

        return api_response(success=True, data=dataset_list)

    except Exception as e:
        current_app.logger.error(f"获取可用数据集列表API错误: {e}")
        return api_error('获取数据集列表失败', 500)

@bp.route('/metric-explanations', methods=['GET'])
@api_auth_required
def api_get_metric_explanations():
    """获取性能指标说明"""
    try:
        metric_explanations = PerformanceEvaluationService.get_metric_explanations()
        percentile_explanations = PerformanceEvaluationService.get_percentile_explanations()

        return api_response(
            success=True,
            data={
                'metric_explanations': metric_explanations,
                'percentile_explanations': percentile_explanations
            }
        )

    except Exception as e:
        current_app.logger.error(f"获取指标说明API错误: {e}")
        return api_error('获取指标说明失败', 500)

@bp.route('/batch-tasks', methods=['POST'])
@api_auth_required
@validate_json_data(['model_id', 'dataset_id', 'test_configurations'])
def api_create_batch_performance_task():
    """创建批量性能评估任务"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        data = request.get_json()

        # 验证模型权限
        model = AIModel.query.filter(
            AIModel.id == data['model_id'],
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).first()

        if not model:
            return api_error('模型未找到或无权限使用', 404)

        # 验证数据集权限（-1表示使用内置openqa数据集）
        if data['dataset_id'] != -1:
            dataset = Dataset.query.filter(
                Dataset.id == data['dataset_id'],
                and_(
                    Dataset.is_active == True,
                    Dataset.dataset_type == '自建',
                    or_(
                        # 自己创建的自建数据集（无论是否公开）
                        Dataset.source == user.username,
                        # 别人创建的公开自建数据集
                        and_(
                            Dataset.source != user.username,
                            Dataset.visibility == '公开'
                        )
                    ),
                    Dataset.format != 'RAG'
                )
            ).first()

            if not dataset:
                return api_error('数据集未找到或无权限使用', 404)

        # 验证测试配置
        test_configurations = data['test_configurations']
        if not isinstance(test_configurations, list) or len(test_configurations) == 0:
            return api_error('测试配置不能为空', 400)

        # 验证每个配置的必要字段
        for i, config in enumerate(test_configurations):
            if not isinstance(config, dict):
                return api_error(f'第{i+1}个测试配置格式错误', 400)

            required_fields = ['concurrency', 'num_requests']
            for field in required_fields:
                if field not in config:
                    return api_error(f'第{i+1}个测试配置缺少必要字段: {field}', 400)

        # 创建批量性能评估任务
        task = BatchPerformanceEvaluationService.create_batch_performance_eval_task(
            user_id=user.id,
            model_id=data['model_id'],
            dataset_id=data['dataset_id'],
            test_configurations=test_configurations,
            name=data.get('name'),
            description=data.get('description')
        )

        if not task:
            return api_error('创建批量性能评估任务失败', 500)

        # 启动批量评估任务
        try:
            BatchPerformanceEvaluationService.run_batch_performance_evaluation(
                task.id,
                data['model_id'],
                data['dataset_id']
            )
        except Exception as e:
            current_app.logger.error(f"启动批量性能评估任务失败: {e}")
            # 如果启动失败，更新任务状态
            task.status = 'failed'
            task.error_message = str(e)
            db.session.commit()
            return api_error(f'启动批量性能评估任务失败: {str(e)}', 500)

        task_dict = {
            'id': task.id,
            'model_name': task.model_name,
            'dataset_name': task.dataset_name,
            'task_type': task.task_type,
            'task_name': task.task_name,
            'status': task.status,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'test_count': len(test_configurations)
        }

        return api_response(
            success=True,
            data=task_dict,
            message='批量性能评估任务创建成功'
        )

    except Exception as e:
        current_app.logger.error(f"创建批量性能评估任务API错误: {e}")
        return api_error('创建批量任务失败', 500)

@bp.route('/batch-tasks/from-script', methods=['POST'])
@api_auth_required
@validate_json_data(['model_id', 'dataset_id', 'num_prompts_list', 'max_concurrency_list', 'input_output_pairs'])
def api_create_batch_task_from_script():
    """从脚本样式参数创建批量性能评估任务（类似 run_1k_4K.sh）"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        data = request.get_json()

        # 验证模型权限
        model = AIModel.query.filter(
            AIModel.id == data['model_id'],
            (AIModel.is_system_model == True) | (AIModel.user_id == user.id)
        ).first()

        if not model:
            return api_error('模型未找到或无权限使用', 404)

        # 验证数据集权限
        if data['dataset_id'] != -1:
            dataset = Dataset.query.filter(
                Dataset.id == data['dataset_id'],
                and_(
                    Dataset.is_active == True,
                    Dataset.dataset_type == '自建',
                    or_(
                        Dataset.source == user.username,
                        and_(
                            Dataset.source != user.username,
                            Dataset.visibility == '公开'
                        )
                    ),
                    Dataset.format != 'RAG'
                )
            ).first()

            if not dataset:
                return api_error('数据集未找到或无权限使用', 404)

        # 解析脚本样式参数
        num_prompts_list = data['num_prompts_list']
        max_concurrency_list = data['max_concurrency_list']
        input_output_pairs = data['input_output_pairs']

        # 验证参数格式
        if not isinstance(num_prompts_list, list) or not isinstance(max_concurrency_list, list):
            return api_error('num_prompts_list 和 max_concurrency_list 必须是数组', 400)

        if len(num_prompts_list) != len(max_concurrency_list):
            return api_error('num_prompts_list 和 max_concurrency_list 长度必须相同', 400)

        if not isinstance(input_output_pairs, list) or len(input_output_pairs) == 0:
            return api_error('input_output_pairs 不能为空', 400)

        # 验证输入输出对格式
        for i, pair in enumerate(input_output_pairs):
            if not isinstance(pair, list) or len(pair) != 2:
                return api_error(f'第{i+1}个输入输出对格式错误，应为[input_len, output_len]', 400)

        # 生成测试配置
        test_configurations = BatchPerformanceEvaluationService.create_configurations_from_script_style(
            num_prompts_list=num_prompts_list,
            max_concurrency_list=max_concurrency_list,
            input_output_pairs=[(pair[0], pair[1]) for pair in input_output_pairs]
        )

        # 生成任务名称
        task_name = data.get('name', f"{model.display_name}_脚本样式压测_{get_beijing_time().strftime('%Y%m%d_%H%M%S')}")

        # 创建批量性能评估任务
        task = BatchPerformanceEvaluationService.create_batch_performance_eval_task(
            user_id=user.id,
            model_id=data['model_id'],
            dataset_id=data['dataset_id'],
            test_configurations=test_configurations,
            name=task_name,
            description=data.get('description', f'基于脚本样式参数的批量压测，共{len(test_configurations)}个测试配置')
        )

        if not task:
            return api_error('创建批量性能评估任务失败', 500)

        # 启动批量评估任务
        try:
            BatchPerformanceEvaluationService.run_batch_performance_evaluation(
                task.id,
                data['model_id'],
                data['dataset_id']
            )
        except Exception as e:
            current_app.logger.error(f"启动批量性能评估任务失败: {e}")
            task.status = 'failed'
            task.error_message = str(e)
            db.session.commit()
            return api_error(f'启动批量性能评估任务失败: {str(e)}', 500)

        task_dict = {
            'id': task.id,
            'model_name': task.model_name,
            'dataset_name': task.dataset_name,
            'task_type': task.task_type,
            'task_name': task.task_name,
            'status': task.status,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'test_count': len(test_configurations),
            'configurations_preview': test_configurations[:3]  # 显示前3个配置作为预览
        }

        return api_response(
            success=True,
            data=task_dict,
            message=f'批量性能评估任务创建成功，共{len(test_configurations)}个测试配置'
        )

    except Exception as e:
        current_app.logger.error(f"从脚本创建批量性能评估任务API错误: {e}")
        return api_error('创建批量任务失败', 500)
