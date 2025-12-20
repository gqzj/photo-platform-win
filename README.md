# 照片管理后台系统

一个基于 React + Python 的照片管理后台系统，包含图片抓取、图片打标、图片统计分析等功能。

## 技术栈

### 前端
- React 18
- Ant Design 5
- React Router 6
- Axios
- Vite

### 后端
- Python 3.8+
- Flask
- SQLAlchemy
- PyMySQL
- Pillow

### 数据库
- MySQL (photo_platform)

## 项目结构

```
photo_platform_new/
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── components/       # 公共组件
│   │   │   └── Layout/      # 布局组件
│   │   ├── pages/           # 页面组件
│   │   │   ├── Dashboard.jsx           # 仪表盘
│   │   │   ├── ImageCapture.jsx        # 图片抓取
│   │   │   ├── ImageTagging.jsx        # 图片打标
│   │   │   └── ImageStatistics.jsx     # 图片统计分析
│   │   ├── services/        # API服务
│   │   ├── App.jsx          # 主应用组件
│   │   └── main.jsx         # 入口文件
│   ├── package.json
│   └── vite.config.js
├── backend/                 # 后端项目
│   ├── app/
│   │   ├── api/             # API路由
│   │   │   ├── image_capture.py        # 图片抓取API
│   │   │   ├── image_tagging.py        # 图片打标API
│   │   │   └── image_statistics.py     # 统计分析API
│   │   ├── models/          # 数据模型
│   │   │   ├── image.py     # 图片模型
│   │   │   ├── tag.py       # 标签模型
│   │   │   └── image_tag.py # 图片标签关联模型
│   │   ├── services/        # 业务逻辑服务
│   │   │   └── image_capture_service.py
│   │   ├── utils/           # 工具函数
│   │   ├── config.py        # 配置文件
│   │   ├── database.py      # 数据库配置
│   │   ├── __init__.py      # 应用工厂
│   │   └── main.py          # 主入口
│   ├── requirements.txt     # Python依赖
│   └── .env.example         # 环境变量示例
└── README.md
```

## 快速开始

### 1. 后端设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，配置数据库连接信息

# 运行后端服务
python app/main.py
```

后端服务将在 `http://localhost:8000` 启动

### 2. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:3000` 启动

## 功能模块

### 1. 图片抓取
- 支持从URL抓取图片
- 批量抓取功能
- 抓取任务管理（开始/暂停/停止）
- 图片信息提取（尺寸、格式等）

### 2. 图片打标
- 图片列表展示
- 单张图片标签编辑
- 批量标签管理
- 标签筛选

### 3. 图片统计分析
- 总图片数统计
- 已打标图片统计
- 标签使用统计
- 时间趋势分析

## API接口

### 图片抓取
- `GET /api/images/capture` - 获取抓取列表
- `POST /api/images/capture/start` - 开始抓取
- `POST /api/images/capture/pause` - 暂停抓取
- `POST /api/images/capture/stop` - 停止抓取

### 图片打标
- `GET /api/images` - 获取图片列表
- `GET /api/images/:id` - 获取图片详情
- `PUT /api/images/:id/tags` - 更新图片标签
- `POST /api/images/batch-tags` - 批量更新标签

### 统计分析
- `GET /api/statistics` - 获取统计数据
- `GET /api/statistics/tags` - 获取标签统计
- `GET /api/statistics/trend` - 获取时间趋势

## 数据库表结构

系统使用以下主要数据表：
- `images` - 图片信息表
- `tags` - 标签表
- `image_tags` - 图片标签关联表

## 开发计划

- [x] 项目结构搭建
- [ ] 图片抓取功能完善
- [ ] 图片打标功能完善
- [ ] 统计分析图表实现
- [ ] 用户认证和权限管理
- [ ] 图片预览和编辑功能
- [ ] 导出功能

## 注意事项

1. 确保MySQL数据库 `photo_platform` 已创建
2. 确保相关数据表已创建
3. 配置 `.env` 文件中的数据库连接信息
4. 图片存储路径需要确保有写入权限

## License

MIT

