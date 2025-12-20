# 数据库配置说明

## 问题
如果遇到数据库连接错误：`Access denied for user 'root'@'localhost' (using password: NO)`

## 解决方法

在 `backend` 目录下创建 `.env` 文件，配置数据库连接信息：

```env
# MySQL数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的数据库密码
MYSQL_DATABASE=photo_platform

# Flask配置
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True

# SQLAlchemy配置
SQLALCHEMY_ECHO=False

# 图片存储路径
IMAGE_STORAGE_PATH=./storage/images
```

**重要**：请将 `MYSQL_PASSWORD=你的数据库密码` 替换为实际的数据库密码。

## 创建步骤

1. 在 `backend` 目录下创建 `.env` 文件
2. 复制上面的配置内容
3. 修改 `MYSQL_PASSWORD` 为你的实际数据库密码
4. 重启后端服务

## 测试连接

配置完成后，可以运行以下命令测试数据库连接：

```bash
cd backend
python test_db_connection.py
```

