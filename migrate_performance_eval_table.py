#!/usr/bin/env python3
"""
数据库迁移脚本：为 PerformanceEvalTask 表添加批量测试支持字段

使用方法:
1. 确保数据库连接正常
2. 运行脚本: python migrate_performance_eval_table.py
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查表中是否存在指定列"""
    try:
        # 使用 PRAGMA table_info 查询表结构（SQLite）
        result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]  # row[1] 是列名
        return column_name in columns
    except Exception as e:
        print(f"检查列是否存在时出错: {e}")
        return False

def add_column_if_not_exists(table_name: str, column_name: str, column_definition: str):
    """如果列不存在则添加列"""
    if check_column_exists(table_name, column_name):
        print(f"✅ 列 {column_name} 已存在，跳过")
        return True
    
    try:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        db.session.execute(text(sql))
        db.session.commit()
        print(f"✅ 成功添加列: {column_name}")
        return True
    except Exception as e:
        print(f"❌ 添加列 {column_name} 失败: {e}")
        db.session.rollback()
        return False

def migrate_database():
    """执行数据库迁移"""
    print("开始数据库迁移...")
    
    table_name = "model_efficiency"
    
    # 要添加的新列
    new_columns = [
        ("task_type", "VARCHAR(20) NOT NULL DEFAULT 'single'"),
        ("task_name", "VARCHAR(200)"),
        ("task_description", "TEXT"),
        ("batch_config", "TEXT"),
        ("batch_results", "TEXT")
    ]
    
    success_count = 0
    
    for column_name, column_definition in new_columns:
        if add_column_if_not_exists(table_name, column_name, column_definition):
            success_count += 1
    
    print(f"\n迁移完成: {success_count}/{len(new_columns)} 个列添加成功")
    
    if success_count == len(new_columns):
        print("✅ 数据库迁移成功完成!")
        return True
    else:
        print("⚠️ 数据库迁移部分完成，请检查错误信息")
        return False

def verify_migration():
    """验证迁移结果"""
    print("\n验证迁移结果...")
    
    table_name = "model_efficiency"
    expected_columns = ["task_type", "task_name", "task_description", "batch_config", "batch_results"]
    
    try:
        result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
        existing_columns = [row[1] for row in result.fetchall()]
        
        print(f"表 {table_name} 的所有列:")
        for col in existing_columns:
            status = "✅" if col in expected_columns else "  "
            print(f"  {status} {col}")
        
        missing_columns = [col for col in expected_columns if col not in existing_columns]
        if missing_columns:
            print(f"\n❌ 缺少的列: {', '.join(missing_columns)}")
            return False
        else:
            print(f"\n✅ 所有新列都已成功添加!")
            return True
            
    except Exception as e:
        print(f"❌ 验证迁移结果时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔧 PerformanceEvalTask 表迁移脚本")
    print("=" * 60)
    
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        try:
            # 检查数据库连接
            db.session.execute(text("SELECT 1"))
            print("✅ 数据库连接正常")
            
            # 执行迁移
            migration_success = migrate_database()
            
            # 验证迁移结果
            verification_success = verify_migration()
            
            if migration_success and verification_success:
                print("\n" + "=" * 60)
                print("🎉 数据库迁移完成!")
                print("现在可以使用批量性能测试功能了。")
                print("=" * 60)
                return True
            else:
                print("\n" + "=" * 60)
                print("❌ 数据库迁移失败!")
                print("请检查错误信息并手动修复。")
                print("=" * 60)
                return False
                
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            print("请确保数据库服务正在运行且配置正确。")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
