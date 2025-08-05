# 数据集管理相关API
from flask import Blueprint, request, current_app
from app.models import Dataset
from app.routes.api.common import (
    api_response, api_error, api_auth_required,
    get_current_api_user, validate_json_data, paginate_query
)
import os
import json
import time
from werkzeug.utils import secure_filename

bp = Blueprint('datasets_api', __name__, url_prefix='/datasets')

@bp.route('', methods=['GET'])
@api_auth_required
def api_get_datasets():
    """获取数据集列表"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 获取查询参数
        search = request.args.get('search', '').strip()
        dataset_type = request.args.get('type', '').strip()

        # 构建查询 - 显示用户自己创建的数据集和公开的数据集
        from sqlalchemy import or_, and_
        query = Dataset.query.filter(
            or_(
                # 自己创建的数据集
                Dataset.source == user.username,
                # 公开的数据集
                and_(
                    Dataset.visibility == '公开',
                    Dataset.source != user.username
                ),
                # 系统数据集
                or_(
                    Dataset.source.is_(None),
                    Dataset.source == '系统'
                )
            )
        )

        # 搜索过滤
        if search:
            query = query.filter(
                Dataset.name.contains(search) |
                Dataset.description.contains(search)
            )

        # 类型过滤
        if dataset_type:
            query = query.filter_by(dataset_type=dataset_type)

        # 排序
        query = query.order_by(Dataset.id.desc())

        # 分页
        pagination_data = paginate_query(query)

        # 序列化数据集数据
        datasets_data = []
        for dataset in pagination_data['items']:
            dataset_dict = {
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description,
                'dataset_type': dataset.dataset_type,
                'file_path': dataset.download_url,  # 使用 download_url 作为文件路径
                'file_size': 0,  # 暂时设为0，因为原模型没有这个字段
                'record_count': 0,  # 暂时设为0，因为原模型没有这个字段
                'created_at': None,  # 原模型没有这个字段
                'updated_at': None,  # 原模型没有这个字段
                'source': dataset.source,
                'visibility': dataset.visibility,
                'format': dataset.format
            }
            datasets_data.append(dataset_dict)

        return api_response(
            success=True,
            data={
                'datasets': datasets_data,
                'total': pagination_data['total']
            }
        )

    except Exception as e:
        current_app.logger.error(f"获取数据集列表API错误: {e}")
        return api_error('获取数据集列表失败', 500)

@bp.route('', methods=['POST'])
@api_auth_required
@validate_json_data(['name', 'dataset_type'])
def api_create_dataset():
    """创建新数据集"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        data = request.get_json()

        # 验证数据集名称唯一性
        existing_dataset = Dataset.query.filter_by(name=data['name']).first()

        if existing_dataset:
            return api_error('数据集名称已存在', 400)

        # 创建数据集
        dataset = Dataset(
            name=data['name'].strip(),
            description=data.get('description', '').strip() or None,
            dataset_type=data['dataset_type'],
            source=user.username,
            visibility=data.get('visibility', '私有'),
            format=data.get('format', 'QA')
        )
        
        from app import db
        db.session.add(dataset)
        db.session.commit()
        
        current_app.logger.info(f"用户 {user.username} 创建数据集: {dataset.name}")
        
        return api_response(
            success=True,
            data={
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description,
                'dataset_type': dataset.dataset_type,
                'created_at': dataset.created_at.isoformat() if dataset.created_at else None
            },
            message='数据集创建成功',
            status_code=201
        )
        
    except Exception as e:
        current_app.logger.error(f"创建数据集API错误: {e}")
        return api_error('创建数据集失败', 500)

@bp.route('/<int:dataset_id>', methods=['GET'])
@api_auth_required
def api_get_dataset(dataset_id):
    """获取单个数据集详情"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 查找数据集
        dataset = Dataset.query.get(dataset_id)

        if not dataset:
            return api_error('数据集未找到', 404)

        # 权限检查
        from sqlalchemy import or_, and_
        has_permission = (
            # 自己创建的数据集
            dataset.source == user.username or
            # 公开的数据集
            dataset.visibility == '公开' or
            # 系统数据集
            dataset.source in [None, '系统']
        )

        if not has_permission:
            return api_error('您没有权限访问此数据集', 403)
        
        dataset_data = {
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'dataset_type': dataset.dataset_type,
            'file_path': dataset.file_path,
            'file_size': dataset.file_size,
            'record_count': dataset.record_count,
            'created_at': dataset.created_at.isoformat() if dataset.created_at else None,
            'updated_at': dataset.updated_at.isoformat() if dataset.updated_at else None
        }
        
        return api_response(success=True, data=dataset_data)
        
    except Exception as e:
        current_app.logger.error(f"获取数据集详情API错误: {e}")
        return api_error('获取数据集详情失败', 500)

@bp.route('/<int:dataset_id>', methods=['DELETE'])
@api_auth_required
def api_delete_dataset(dataset_id):
    """删除数据集"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 查找数据集
        dataset = Dataset.query.get(dataset_id)

        if not dataset:
            return api_error('数据集未找到', 404)

        # 权限检查 - 只能删除自己创建的数据集
        if dataset.source != user.username:
            return api_error('您只能删除自己创建的数据集', 403)

        dataset_name = dataset.name

        # 删除数据集文件（如果存在）
        if dataset.download_url and os.path.exists(dataset.download_url):
            import os
            try:
                os.remove(dataset.download_url)
            except Exception as e:
                current_app.logger.warning(f"删除数据集文件失败: {e}")

        # 删除数据库记录
        from app import db
        db.session.delete(dataset)
        db.session.commit()

        current_app.logger.info(f"用户 {user.username} 删除数据集: {dataset_name}")

        return api_response(
            success=True,
            message=f'数据集 "{dataset_name}" 删除成功'
        )

    except Exception as e:
        current_app.logger.error(f"删除数据集API错误: {e}")
        return api_error('删除数据集失败', 500)

@bp.route('/<int:dataset_id>/data', methods=['GET'])
@api_auth_required
def api_get_dataset_data(dataset_id):
    """获取数据集数据（预览）"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 查找数据集
        dataset = Dataset.query.get(dataset_id)

        if not dataset:
            return api_error('数据集未找到', 404)

        # 权限检查
        has_permission = (
            # 自己创建的数据集
            dataset.source == user.username or
            # 公开的数据集
            dataset.visibility == '公开' or
            # 系统数据集
            dataset.source in [None, '系统']
        )

        if not has_permission:
            return api_error('您没有权限访问此数据集', 403)

        if not dataset.download_url:
            return api_error('数据集文件不存在', 404)
        
        # 读取数据集文件（限制预览行数）
        limit = int(request.args.get('limit', 100))
        limit = min(limit, 1000)  # 最大1000行

        try:
            import json
            import os

            file_path = dataset.download_url
            if not file_path or not os.path.exists(file_path):
                return api_error('数据集文件不存在', 404)

            data_preview = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    try:
                        data_preview.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue

            return api_response(
                success=True,
                data={
                    'preview': data_preview,
                    'total_shown': len(data_preview),
                    'total_records': len(data_preview),  # 暂时使用预览数据长度
                    'limit': limit
                }
            )
            
        except Exception as e:
            current_app.logger.error(f"读取数据集文件错误: {e}")
            return api_error('读取数据集文件失败', 500)
        
    except Exception as e:
        current_app.logger.error(f"获取数据集数据API错误: {e}")
        return api_error('获取数据集数据失败', 500)

@bp.route('/upload', methods=['POST'])
@api_auth_required
def api_upload_dataset():
    """上传数据集文件"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 检查文件
        if 'file' not in request.files:
            return api_error('未找到上传文件', 400)

        file = request.files['file']
        if file.filename == '':
            return api_error('未选择文件', 400)

        # 获取表单数据
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        dataset_type = request.form.get('dataset_type', '').strip()

        if not name or not dataset_type:
            return api_error('数据集名称和类型不能为空', 400)

        # 验证数据集名称唯一性
        existing_dataset = Dataset.query.filter_by(name=name).first()

        if existing_dataset:
            return api_error('数据集名称已存在', 400)

        # 验证文件类型
        if not file.filename.lower().endswith(('.json', '.jsonl')):
            return api_error('只支持JSON和JSONL格式文件', 400)

        # 创建上传目录
        upload_dir = current_app.config.get('DATA_UPLOADS_DIR', 'data/uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # 生成安全的文件名
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        safe_filename = f"{user.id}_{timestamp}_{filename}"
        file_path = os.path.join(upload_dir, safe_filename)

        # 保存文件
        file.save(file_path)

        # 分析文件内容
        try:
            record_count = 0
            file_size = os.path.getsize(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            json.loads(line)
                            record_count += 1
                        except json.JSONDecodeError:
                            continue

            # 创建数据集记录
            dataset = Dataset(
                name=name,
                description=description or None,
                dataset_type=dataset_type,
                download_url=file_path,
                source=user.username,
                visibility='私有',  # 默认为私有
                format='QA'  # 默认格式
            )

            from app import db
            db.session.add(dataset)
            db.session.commit()

            current_app.logger.info(f"用户 {user.username} 上传数据集: {dataset.name}")

            return api_response(
                success=True,
                data={
                    'id': dataset.id,
                    'name': dataset.name,
                    'description': dataset.description,
                    'dataset_type': dataset.dataset_type,
                    'file_size': file_size,
                    'record_count': record_count,
                    'created_at': None  # 原模型没有这个字段
                },
                message='数据集上传成功',
                status_code=201
            )

        except Exception as e:
            # 如果处理失败，删除已上传的文件
            try:
                os.remove(file_path)
            except:
                pass
            raise e

    except Exception as e:
        current_app.logger.error(f"上传数据集API错误: {e}")
        return api_error('上传数据集失败', 500)

@bp.route('/<int:dataset_id>/preview', methods=['GET'])
@api_auth_required
def api_preview_dataset(dataset_id):
    """预览数据集"""
    try:
        user = get_current_api_user()
        if not user:
            return api_error('用户未找到', 404)

        # 查找数据集
        dataset = Dataset.query.get(dataset_id)

        if not dataset:
            return api_error('数据集未找到', 404)

        # 权限检查
        has_permission = (
            # 自己创建的数据集
            dataset.source == user.username or
            # 公开的数据集
            dataset.visibility == '公开' or
            # 系统数据集
            dataset.source in [None, '系统']
        )

        if not has_permission:
            return api_error('您没有权限访问此数据集', 403)

        # 如果是本地文件，读取预览数据
        if dataset.download_url and os.path.exists(dataset.download_url):
            try:
                import json
                data_preview = []
                with open(dataset.download_url, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if i >= 10:  # 只预览前10行
                            break
                        try:
                            data_preview.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue

                return api_response(
                    success=True,
                    data={
                        'preview': data_preview,
                        'total_shown': len(data_preview)
                    }
                )
            except Exception as e:
                current_app.logger.error(f"读取数据集文件错误: {e}")
                return api_error('读取数据集文件失败', 500)
        else:
            # 如果没有本地文件，返回空预览
            return api_response(
                success=True,
                data={
                    'preview': [],
                    'total_shown': 0
                }
            )

    except Exception as e:
        current_app.logger.error(f"预览数据集API错误: {e}")
        return api_error('预览数据集失败', 500)
