import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("后端服务启动")
    print("=" * 60)
    print(f"日志文件位置: {os.path.join(os.path.dirname(__file__), '..', 'logs')}")
    print("=" * 60)
    # 禁用use_reloader以避免Playwright文件变化触发重启
    app.run(debug=True, host='0.0.0.0', port=8000, use_reloader=False)

