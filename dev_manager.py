#!/usr/bin/env python3
"""
LLM评估平台开发环境管理器
一个简单的命令行面板，用于启动和停止前后端服务
"""

import os
import sys
import subprocess
import time
import signal
import psutil
import webbrowser
from pathlib import Path

class DevManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.project_root = Path(__file__).parent
        
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_menu(self):
        """显示主菜单"""
        self.clear_screen()
        print("=" * 50)
        print("    LLM评估平台 - 开发环境管理器")
        print("=" * 50)
        print()
        
        # 检查服务状态
        backend_status = "🟢 运行中" if self.is_backend_running() else "🔴 已停止"
        frontend_status = "🟢 运行中" if self.is_frontend_running() else "🔴 已停止"
        
        print(f"后端服务 (Flask):  {backend_status}")
        print(f"前端服务 (Vue):    {frontend_status}")
        print()
        print("请选择操作:")
        print("1. 启动后端服务")
        print("2. 启动前端服务")
        print("3. 启动全部服务")
        print("4. 停止后端服务")
        print("5. 停止前端服务")
        print("6. 停止全部服务")
        print("7. 打开前端页面")
        print("8. 查看服务状态")
        print("9. 检查环境")
        print("0. 退出")
        print("=" * 50)
    
    def is_backend_running(self):
        """检查后端是否运行"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'run_api.py' in cmdline or 'run_api_simple.py' in cmdline:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def is_frontend_running(self):
        """检查前端是否运行"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'node.exe' or proc.info['name'] == 'node':
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'vite' in cmdline.lower():
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def find_python_command(self):
        """查找Python命令"""
        python_commands = ['python', 'python3', 'py']

        for cmd in python_commands:
            try:
                result = subprocess.run([cmd, '--version'],
                                      capture_output=True,
                                      check=True,
                                      timeout=5)
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def start_backend(self):
        """启动后端服务"""
        if self.is_backend_running():
            print("后端服务已在运行中")
            return

        # 优先使用简化版启动脚本
        api_files = ['run_api_simple.py', 'run_api.py']
        api_file = None
        for filename in api_files:
            file_path = self.project_root / filename
            if file_path.exists():
                api_file = filename
                break

        if not api_file:
            print("❌ 未找到后端启动文件 (run_api_simple.py 或 run_api.py)")
            return

        # 查找可用的Python命令
        python_cmd = self.find_python_command()
        if not python_cmd:
            print("❌ 未找到Python，请先安装Python")
            print("   下载地址: https://www.python.org/downloads/")
            return

        print(f"启动后端服务 (使用 {python_cmd} {api_file})...")
        try:
            if os.name == 'nt':  # Windows
                self.backend_process = subprocess.Popen(
                    [python_cmd, api_file],
                    cwd=self.project_root,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:  # Linux/Mac
                self.backend_process = subprocess.Popen(
                    [python_cmd, api_file],
                    cwd=self.project_root
                )
            print("✅ 后端服务启动成功 (端口: 5000)")
            time.sleep(2)
        except Exception as e:
            print(f"❌ 后端服务启动失败: {e}")
            print("   请确保已安装Python和项目依赖")
    
    def find_npm_command(self):
        """查找npm命令"""
        npm_commands = ['npm', 'npm.cmd', 'pnpm', 'pnpm.cmd', 'yarn', 'yarn.cmd']

        for cmd in npm_commands:
            try:
                subprocess.run([cmd, '--version'],
                             capture_output=True,
                             check=True,
                             timeout=5)
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def start_frontend(self):
        """启动前端服务"""
        if self.is_frontend_running():
            print("前端服务已在运行中")
            return

        frontend_dir = self.project_root / 'llm-eval-frontend'
        if not frontend_dir.exists():
            print("❌ 前端目录不存在")
            return

        # 查找可用的包管理器
        npm_cmd = self.find_npm_command()
        if not npm_cmd:
            print("❌ 未找到npm/pnpm/yarn，请先安装Node.js")
            print("   下载地址: https://nodejs.org/")
            return

        print(f"启动前端服务 (使用 {npm_cmd})...")
        try:
            if os.name == 'nt':  # Windows
                self.frontend_process = subprocess.Popen(
                    [npm_cmd, 'run', 'dev'],
                    cwd=frontend_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    shell=True
                )
            else:  # Linux/Mac
                self.frontend_process = subprocess.Popen(
                    [npm_cmd, 'run', 'dev'],
                    cwd=frontend_dir
                )
            print("✅ 前端服务启动成功 (端口: 3000)")
            time.sleep(3)
        except Exception as e:
            print(f"❌ 前端服务启动失败: {e}")
            print("   请确保已安装Node.js和项目依赖")
    
    def stop_backend(self):
        """停止后端服务"""
        print("停止后端服务...")
        killed = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'run_api.py' in cmdline or 'run_api_simple.py' in cmdline:
                        proc.terminate()
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed:
            print("✅ 后端服务已停止")
        else:
            print("ℹ️ 未发现运行中的后端服务")
    
    def stop_frontend(self):
        """停止前端服务"""
        print("停止前端服务...")
        killed = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'node.exe' or proc.info['name'] == 'node':
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'vite' in cmdline.lower():
                        proc.terminate()
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed:
            print("✅ 前端服务已停止")
        else:
            print("ℹ️ 未发现运行中的前端服务")
    
    def open_frontend(self):
        """打开前端页面"""
        print("打开前端页面...")
        webbrowser.open('http://localhost:3000')
        print("✅ 已在浏览器中打开前端页面")
    
    def show_status(self):
        """显示详细状态"""
        print("\n服务状态详情:")
        print("-" * 30)
        
        backend_running = self.is_backend_running()
        frontend_running = self.is_frontend_running()
        
        print(f"后端服务: {'🟢 运行中' if backend_running else '🔴 已停止'}")
        if backend_running:
            print("  - 地址: http://localhost:5000")
            print("  - 健康检查: http://localhost:5000/health")
        
        print(f"前端服务: {'🟢 运行中' if frontend_running else '🔴 已停止'}")
        if frontend_running:
            print("  - 地址: http://localhost:3000")
        
        print("\n默认账户:")
        print("  - 管理员: admin/admin")
        print("  - 测试用户: test/test")

    def check_environment(self):
        """检查开发环境"""
        print("\n环境检查:")
        print("-" * 30)

        # 检查Python
        python_cmd = self.find_python_command()
        if python_cmd:
            try:
                result = subprocess.run([python_cmd, '--version'],
                                      capture_output=True, text=True)
                print(f"✅ Python: {result.stdout.strip()} ({python_cmd})")
            except:
                print(f"⚠️ Python: 找到命令但无法获取版本 ({python_cmd})")
        else:
            print("❌ Python: 未安装")

        # 检查Node.js
        npm_cmd = self.find_npm_command()
        if npm_cmd:
            try:
                # 检查Node版本
                result = subprocess.run(['node', '--version'],
                                      capture_output=True, text=True)
                node_version = result.stdout.strip()

                # 检查包管理器版本
                result = subprocess.run([npm_cmd, '--version'],
                                      capture_output=True, text=True)
                npm_version = result.stdout.strip()

                print(f"✅ Node.js: {node_version}")
                print(f"✅ 包管理器: {npm_cmd} {npm_version}")
            except:
                print(f"⚠️ Node.js: 找到包管理器但无法获取版本 ({npm_cmd})")
        else:
            print("❌ Node.js: 未安装")

        # 检查项目文件
        print("\n项目文件:")
        api_simple_file = self.project_root / 'run_api_simple.py'
        api_file = self.project_root / 'run_api.py'
        frontend_dir = self.project_root / 'llm-eval-frontend'

        if api_simple_file.exists():
            print("✅ 后端文件: run_api_simple.py (推荐)")
        elif api_file.exists():
            print("✅ 后端文件: run_api.py")
        else:
            print("❌ 后端文件: 未找到启动文件")
        print(f"{'✅' if frontend_dir.exists() else '❌'} 前端目录: llm-eval-frontend/")

        if frontend_dir.exists():
            package_json = frontend_dir / 'package.json'
            node_modules = frontend_dir / 'node_modules'
            print(f"{'✅' if package_json.exists() else '❌'} 前端配置: package.json")
            print(f"{'✅' if node_modules.exists() else '❌'} 前端依赖: node_modules/")

            if not node_modules.exists() and npm_cmd:
                print(f"\n💡 提示: 运行 'cd llm-eval-frontend && {npm_cmd} install' 安装前端依赖")
    
    def run(self):
        """运行主循环"""
        while True:
            self.show_menu()
            
            try:
                choice = input("请输入选项 (0-9): ").strip()
                
                if choice == '0':
                    print("退出程序...")
                    break
                elif choice == '1':
                    self.start_backend()
                elif choice == '2':
                    self.start_frontend()
                elif choice == '3':
                    self.start_backend()
                    self.start_frontend()
                elif choice == '4':
                    self.stop_backend()
                elif choice == '5':
                    self.stop_frontend()
                elif choice == '6':
                    self.stop_backend()
                    self.stop_frontend()
                elif choice == '7':
                    self.open_frontend()
                elif choice == '8':
                    self.show_status()
                elif choice == '9':
                    self.check_environment()
                else:
                    print("无效选项，请重新选择")
                
                if choice != '0':
                    input("\n按回车键继续...")
                    
            except KeyboardInterrupt:
                print("\n\n程序被中断，正在退出...")
                break
            except Exception as e:
                print(f"发生错误: {e}")
                input("按回车键继续...")

if __name__ == '__main__':
    # 检查依赖
    try:
        import psutil
    except ImportError:
        print("缺少依赖包 psutil，正在安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
        import psutil
    
    manager = DevManager()
    manager.run()
