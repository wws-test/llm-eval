#!/usr/bin/env python3
"""
最简单的API服务器启动脚本
"""

import os
import sys

# 设置环境变量
os.environ['FLASK_APP'] = 'app'
os.environ['FLASK_ENV'] = 'development'

if __name__ == '__main__':
    # 使用Flask CLI启动
    from flask.cli import main
    sys.argv = ['flask', 'run', '--host=0.0.0.0', '--port=5000', '--debug']
    main()
