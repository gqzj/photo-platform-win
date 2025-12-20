"""检查配置是否正确加载"""
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

print("=" * 50)
print("数据库配置检查")
print("=" * 50)
print(f"MYSQL_HOST: {os.getenv('MYSQL_HOST', 'NOT SET')}")
print(f"MYSQL_PORT: {os.getenv('MYSQL_PORT', 'NOT SET')}")
print(f"MYSQL_USER: {os.getenv('MYSQL_USER', 'NOT SET')}")
print(f"MYSQL_PASSWORD: {'***' if os.getenv('MYSQL_PASSWORD') else 'NOT SET (空)'}")
print(f"MYSQL_DATABASE: {os.getenv('MYSQL_DATABASE', 'NOT SET')}")
print("=" * 50)

# 检查.env文件路径
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"\n.env文件路径: {env_path}")
print(f".env文件存在: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print("\n.env文件内容（隐藏密码）:")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'PASSWORD' in line:
                # 隐藏密码
                if '=' in line:
                    key = line.split('=')[0]
                    print(f"{key}=***")
                else:
                    print(line.strip())
            else:
                print(line.strip())

