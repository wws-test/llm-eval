from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, jsonify # Added jsonify
from flask_login import login_required, current_user # 添加用户认证相关导入
from app import db # 数据库实例
from app.models import Dataset, DatasetCategory # 数据模型
from app.forms import CustomDatasetForm # Import the new form
from app.services.dataset_service import DatasetService
import json # For parsing sample_data_json
import os # For os.path.join
from werkzeug.utils import secure_filename # For secure filenames
import math # 用于分页计算
from datetime import datetime
from sqlalchemy import or_, and_

# 创建一个名为 'datasets' 的蓝图
bp = Blueprint('datasets', __name__, url_prefix='/datasets')

@bp.route('/system')
def datasets_list():
    """
    显示数据集列表，支持按分类筛选。
    权限控制：
    1. 自己创建的所有数据集（无论是否公开）
    2. 别人创建的公开数据集
    3. 系统数据集
    默认只显示已激活的数据集，通过show_all参数可显示所有数据集。
    """
    selected_category_name = request.args.get('category', '全部') # 默认为'全部'
    show_all = request.args.get('show_all', '0') == '1' # 默认不显示所有数据集
    
    all_db_categories = DatasetCategory.query.order_by(DatasetCategory.name).all()
    
    query = Dataset.query
    
    # 如果不显示所有数据集，则只返回已激活的数据集
    if not show_all:
        query = query.filter(Dataset.is_active == True)
    
    # 权限过滤：只显示有权限查看的数据集
    if current_user and current_user.is_authenticated:
        query = query.filter(
            or_(
                # 自己创建的所有数据集
                Dataset.source == current_user.username,
                # 别人创建的公开数据集
                and_(
                    Dataset.source != current_user.username,
                    Dataset.visibility == '公开'
                ),
                # 系统数据集（source为空或为'系统'）
                or_(
                    Dataset.source.is_(None),
                    Dataset.source == '系统'
                )
            )
        )
    else:
        # 未登录用户只能看到公开数据集和系统数据集
        query = query.filter(
            or_(
                Dataset.visibility == '公开',
                Dataset.source.is_(None),
                Dataset.source == '系统'
            )
        )
    
    if selected_category_name != '全部' and selected_category_name:
        query = query.join(Dataset.categories).filter(DatasetCategory.name == selected_category_name)
        
    datasets_from_db = query.order_by(Dataset.name).all()
    
    return render_template(
        'datasets/datasets.html', 
        datasets=datasets_from_db, 
        all_categories=all_db_categories,
        selected_category=selected_category_name,
        show_all=show_all
    ) 

@bp.route('/custom/add', methods=['GET', 'POST'])
@login_required
def add_custom_dataset():
    form = CustomDatasetForm()
    # Populate category choices dynamically
    form.categories.choices = [(cat.id, cat.name) for cat in DatasetCategory.query.order_by('name').all()]

    if form.validate_on_submit():
        try:
            # 检查数据集名称在当前用户内的唯一性
            dataset_name = form.name.data.strip()
            existing_dataset = Dataset.query.filter_by(
                name=dataset_name,
                dataset_type='自建',
                source=current_user.username
            ).first()
            
            if existing_dataset:
                flash(f'数据集名称 "{dataset_name}" 已存在，请使用其他名称。', 'error')
                return render_template('datasets/add_custom_dataset.html', title='添加自定义数据集', form=form)
            
            if form.jinja2_template.data:
                # 验证Jinja2模板是否包含所需的宏
                required_macros = ['gen_prompt', 'get_gold_answer', 'match', 'parse_pred_result', 'compute_metric']
                template_content = form.jinja2_template.data
                missing_macros = []
                for macro in required_macros:
                    if f'macro {macro}' not in template_content:
                        missing_macros.append(macro)
                
                if missing_macros:
                    flash(f'Jinja2模板缺少以下必需的宏：{", ".join(missing_macros)}', 'error')
                    return render_template('datasets/add_custom_dataset.html', title='添加自定义数据集', form=form)
                
            # Process categories from selected IDs
            category_objects = []
            if form.categories.data:
                category_objects = DatasetCategory.query.filter(DatasetCategory.id.in_(form.categories.data)).all()
            
            # 处理文件上传
            if form.dataset_file.data:
                file = form.dataset_file.data
                if file and file.filename:
                    # 确保文件名安全
                    filename = secure_filename(file.filename)
                    # 创建用户特定的上传目录
                    upload_dir = os.path.join(current_app.config['DATA_UPLOADS_DIR'], current_user.username)
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # 生成新的文件名（添加时间戳以避免重名）
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    new_filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(upload_dir, new_filename)
                    
                    # 保存文件
                    file.save(file_path)
                    
                    # 根据文件类型处理数据
                    if filename.endswith('.jsonl'):
                        # 处理JSONL文件
                        validated_lines = 0
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f):
                                if i >= 5:  # 只检查前5行
                                    break
                                try:
                                    json.loads(line.strip())
                                    validated_lines += 1
                                except json.JSONDecodeError:
                                    continue
                        
                        # 检查是否有有效数据
                        if validated_lines == 0:
                            flash('文件为空或前5行没有有效的数据', 'error')
                            return render_template('datasets/add_custom_dataset.html', title='添加自定义数据集', form=form)
                        
                        # 创建数据集结构信息
                        subset_name = os.path.splitext(new_filename)[0]
                        dataset_info_data = {
                            subset_name: {
                                "features": {
                                    "system": {"dtype": "string", "id": None, "_type": "Value"},
                                    "query": {"dtype": "string", "id": None, "_type": "Value"},
                                    "response": {"dtype": "string", "id": None, "_type": "Value"}
                                },
                                "splits": {
                                    "test": {
                                        "name": "test", 
                                        "dataset_name": subset_name
                                    }
                                }
                            }
                        }
                    elif filename.endswith('.csv'):
                        # 处理CSV文件
                        import pandas as pd
                        try:
                            df = pd.read_csv(file_path)
                            # 验证CSV文件格式
                            required_columns = ['question', 'answer']
                            option_columns = [col for col in df.columns if col in ['A', 'B', 'C', 'D']]
                            
                            if not all(col in df.columns for col in required_columns):
                                flash('CSV文件必须包含question和answer列', 'error')
                                return render_template('datasets/add_custom_dataset.html', title='添加自定义数据集', form=form)
                            
                            if not option_columns:
                                flash('CSV文件必须包含A、B、C、D选项列', 'error')
                                return render_template('datasets/add_custom_dataset.html', title='添加自定义数据集', form=form)
                            
                            # 动态创建features，包含所有检测到的选项列
                            features = {
                                "id": {"dtype": "int32", "id": None, "_type": "Value"},
                                "question": {"dtype": "string", "id": None, "_type": "Value"}
                            }
                            # 添加选项列
                            for option in option_columns:
                                features[option] = {"dtype": "string", "id": None, "_type": "Value"}
                            features["answer"] = {"dtype": "string", "id": None, "_type": "Value"}
                            
                            dataset_info_data = {
                                subset_name: {
                                    "features": features,
                                    "splits": {
                                        "test": {
                                            "name": "test", 
                                            "dataset_name": subset_name
                                        }
                                    }
                                }
                            }
                        except Exception as e:
                            flash(f'处理CSV文件时出错：{str(e)}', 'error')
                            return render_template('datasets/add_custom_dataset.html', title='添加自定义数据集', form=form)
                else:
                    flash('上传的文件名无效。', 'warning')
            else:
                flash('请上传数据集文件。', 'error')
                return render_template('datasets/add_custom_dataset.html', title='添加自定义数据集', form=form)
            
            # 处理发布日期，如果为空则设置为当前日期
            publish_date = form.publish_date.data
            if not publish_date or publish_date.strip() == '':
                publish_date = datetime.now().strftime('%Y-%m-%d')
            
            new_dataset = Dataset(
                name=form.name.data,
                description=form.description.data,
                publish_date=publish_date,
                source=current_user.username,
                download_url=file_path,
                dataset_info=json.dumps(dataset_info_data) if dataset_info_data else None,
                dataset_type='自建',
                visibility=form.visibility.data,
                format=form.format.data,
                jinja2_template=form.jinja2_template.data if form.format.data == 'CUSTOM' else None,
                categories=category_objects
            )
            db.session.add(new_dataset)
            db.session.commit()
            flash(f'自定义数据集 " {new_dataset.name} " 已成功添加!', 'success')
            return redirect(url_for('datasets.datasets_list'))
        except ValueError as ve:
            current_app.logger.error(f"Error adding custom dataset: {ve}")
            flash(f'添加数据集失败: {ve}', 'error')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding custom dataset: {e}")
            flash(f'添加数据集时发生错误，请稍后重试或联系管理员。', 'error')
            
    # For GET request or if form validation failed, re-render with choices populated
    if not form.categories.choices: # Ensure choices are set if validation failed and it's a POST
        form.categories.choices = [(cat.id, cat.name) for cat in DatasetCategory.query.order_by('name').all()]
        
    return render_template('datasets/add_custom_dataset.html', title='添加自定义数据集', form=form) 

@bp.route('/<int:dataset_id>/data')
def list_dataset_data(dataset_id):
    """
    API端点：异步获取数据集预览数据
    权限控制：只允许访问有权限的数据集
    """
    # 获取数据集信息
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # 权限检查
    if current_user and current_user.is_authenticated:
        # 检查是否有权限访问此数据集
        has_permission = (
            # 自己创建的数据集
            dataset.source == current_user.username or
            # 公开的数据集
            dataset.visibility == '公开' or
            # 系统数据集
            dataset.source in [None, '系统']
        )
        if not has_permission:
            return jsonify({'error': '您没有权限访问此数据集'}), 403
    else:
        # 未登录用户只能访问公开数据集和系统数据集
        if dataset.visibility != '公开' and dataset.source not in [None, '系统']:
            return jsonify({'error': '您没有权限访问此数据集'}), 403
    
    # 获取筛选参数
    subset = request.args.get('subset', '')
    split = request.args.get('split', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 每页显示20条数据
    
    # 使用DatasetService获取数据集数据
    data, total_items = DatasetService.get_dataset_data(
        dataset.dataset_info or {}, 
        subset, 
        split, 
        dataset.download_url,
        page, 
        per_page
    )
    
    # 计算总页数
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
    
    # 计算分页范围
    start_page = max(1, page - 2)
    end_page = min(total_pages + 1, page + 3) if total_pages > 0 else 1
    page_range = list(range(start_page, end_page))
    
    print(f'field_order: {list(data[0].keys()) if data else []}')
    return jsonify({
        'data': data,
        'field_order': list(data[0].keys()) if data else [],  # 添加字段顺序信息
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'page_range': page_range
        }
    })

@bp.route('/preview/<int:dataset_id>')
def preview_dataset(dataset_id):
    """
    预览数据集内容，支持筛选子数据集和用途。
    权限控制：只允许访问有权限的数据集
    使用异步加载方式获取数据集数据。
    """
    # 获取数据集信息
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # 权限检查
    if current_user and current_user.is_authenticated:
        # 检查是否有权限访问此数据集
        has_permission = (
            # 自己创建的数据集
            dataset.source == current_user.username or
            # 公开的数据集
            dataset.visibility == '公开' or
            # 系统数据集
            dataset.source in [None, '系统']
        )
        if not has_permission:
            flash('您没有权限访问此数据集', 'error')
            return redirect(url_for('datasets.datasets_list'))
    else:
        # 未登录用户只能访问公开数据集和系统数据集
        if dataset.visibility != '公开' and dataset.source not in [None, '系统']:
            flash('您没有权限访问此数据集', 'error')
            return redirect(url_for('datasets.datasets_list'))
    
    # 获取筛选参数
    subset = request.args.get('subset', '')
    split = request.args.get('split', '')
    page = request.args.get('page', 1, type=int)
    
    # 使用DatasetService获取数据集结构信息
    subsets, splits_by_subset = DatasetService.get_dataset_structure(dataset.dataset_info or {})
    
    # 调试日志
    current_app.logger.info(f"数据集结构: subsets={subsets}, splits_by_subset={splits_by_subset}")
    
    # 如果未指定子数据集但有可用的子数据集，则使用第一个
    if not subset and subsets:
        subset = subsets[0]
    
    # 如果未指定split但当前子数据集有可用的split，则使用第一个
    available_splits = splits_by_subset.get(subset, [])
    if not split and available_splits:
        split = available_splits[0]
    
    # 调试日志
    current_app.logger.info(f"当前选择: subset={subset}, split={split}")
    current_app.logger.info(f"current_subset在splits_by_subset中: {subset in splits_by_subset}")
    
    # 渲染预览页面 - 不再直接加载数据，改为前端异步加载
    return render_template(
        'datasets/preview_dataset.html',
        dataset=dataset,
        subsets=subsets,
        splits_by_subset=splits_by_subset,
        current_subset=subset,
        current_split=split,
        page=page
    ) 

@bp.route('/<int:dataset_id>/toggle_active', methods=['POST'])
def toggle_dataset_active(dataset_id):
    """
    API端点：切换数据集的启用/禁用状态
    """
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # 切换状态
    dataset.is_active = not dataset.is_active
    
    try:
        db.session.commit()
        status = "启用" if dataset.is_active else "禁用"
        return jsonify({
            'success': True,
            'is_active': dataset.is_active,
            'message': f'数据集 "{dataset.name}" 已{status}'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"切换数据集状态失败: {e}")
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500

@bp.route('/<int:dataset_id>/delete', methods=['DELETE'])
@login_required
def delete_dataset(dataset_id):
    """
    API端点：删除自建数据集
    只允许用户删除自己创建的自建数据集
    """
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # 权限检查：只能删除自己创建的自建数据集
    if dataset.dataset_type != '自建':
        return jsonify({
            'success': False,
            'message': '只能删除自建数据集'
        }), 403
    
    if dataset.source != current_user.username:
        return jsonify({
            'success': False,
            'message': '您只能删除自己创建的数据集'
        }), 403
    
    # 获取强制删除参数
    force_delete = request.json.get('force', False) if request.json else False
    
    try:
        # 检查是否有评估记录引用此数据集
        evaluation_records = dataset.evaluations.all()
        # 检查是否有评估结果记录引用此数据集
        evaluation_result_records = dataset.evaluation_results.all()
        
        total_dependencies = len(evaluation_records) + len(evaluation_result_records)
        
        if (evaluation_records or evaluation_result_records) and not force_delete:
            return jsonify({
                'success': False,
                'message': f'无法删除数据集 "{dataset.name}"，因为有 {total_dependencies} 个相关记录正在使用此数据集。',
                'has_dependencies': True,
                'dependency_count': total_dependencies
            }), 400
        
        # 如果强制删除，先删除相关的记录
        if force_delete:
            # 删除相关的评估结果记录
            if evaluation_result_records:
                for result_record in evaluation_result_records:
                    db.session.delete(result_record)
                current_app.logger.info(f"已删除 {len(evaluation_result_records)} 个相关的评估结果记录")
            
            # 删除相关的评估数据集记录
            if evaluation_records:
                for eval_dataset_record in evaluation_records:
                    db.session.delete(eval_dataset_record)
                current_app.logger.info(f"已删除 {len(evaluation_records)} 个相关的评估数据集记录")
        
        # 删除关联的文件
        if dataset.download_url and os.path.exists(dataset.download_url):
            try:
                os.remove(dataset.download_url)
                current_app.logger.info(f"已删除数据集文件: {dataset.download_url}")
            except Exception as file_error:
                current_app.logger.warning(f"删除数据集文件失败: {file_error}")
                # 文件删除失败不影响数据库记录删除
        
        dataset_name = dataset.name
        
        # 删除数据库记录
        db.session.delete(dataset)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'数据集 "{dataset_name}" 已成功删除'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除数据集失败: {e}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500 