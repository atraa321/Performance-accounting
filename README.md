# 医院科室绩效核算系统

基于 FastAPI + React 的医院科室绩效核算管理系统。

## 快速启动

### 1. 一键启动（推荐）

```powershell
.\启动.ps1
```

系统会自动：
- 初始化数据库（首次运行）
- 安装前端依赖（首次运行）
- 启动后端服务（端口 8000）
- 启动前端服务（端口 3000）
- 打开浏览器

### 2. 停止服务

```powershell
.\停止.ps1
```

### 3. 手动启动

**后端**（终端 1）：
```powershell
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**前端**（终端 2）：
```powershell
cd frontend
npm run dev
```

## 访问地址

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8001
- **API 文档**: http://localhost:8001/docs

## 系统要求

- Python 3.8+
- Node.js 16+
- npm 8+

## 主要功能

### 1. 批次管理
- 创建核算批次
- 导入 Excel 数据（多 Sheet 支持）
- 执行绩效计算
- 导出计算结果

### 2. 规则参数管理
- 直接发放规则配置
- 奖金池分配规则配置
- 结余分配规则配置
- 参数批量更新

### 3. 项目映射管理
- 收入项目映射
- 成本项目映射
- 工作量项目映射
- 批量导入导出

### 4. 审计日志
- 操作记录追踪
- 数据变更历史
- 用户行为审计

## 技术栈

### 后端
- FastAPI - Web 框架
- SQLAlchemy - ORM
- Alembic - 数据库迁移
- Pydantic - 数据验证
- openpyxl - Excel 处理

### 前端
- React 18
- TypeScript
- Vite
- Ant Design
- Axios

### 数据库
- SQLite（开发）
- MySQL（生产）

## 项目结构

```
科室绩效核算v2/
├── app/                    # 后端代码
│   ├── api/               # API 路由
│   ├── calc/              # 计算引擎
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   └── schemas/           # 数据模式
├── frontend/              # 前端代码
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # 组件
│   │   └── pages/        # 页面
│   └── package.json
├── alembic/               # 数据库迁移
├── docs/                  # 开发文档
├── samples/               # 示例文件
├── tests/                 # 测试文件
├── 文档/                  # 项目文档
│   ├── 更新日志.md
│   ├── 启动指南.md
│   ├── 批次删除功能.md
│   ├── 数据导入规则更新.md
│   └── ...
├── 脚本/                  # 辅助脚本
│   ├── 测试后端.ps1
│   ├── 测试前端.ps1
│   └── 检查状态.ps1
├── 启动.ps1               # 一键启动脚本
├── 停止.ps1               # 停止服务脚本
├── README.md              # 项目说明
└── requirements.txt       # Python 依赖
```

## 开发指南

### 后端开发

```powershell
# 安装依赖
pip install -r requirements.txt

# 报表 PDF 导出（B 方案：HTML → PDF）需要安装 Chromium（仅本机开发/非 Docker 场景）
python -m playwright install chromium

# 创建数据库迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 运行测试
pytest
```

### 前端开发

```powershell
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

## 配置说明

### 数据库配置

编辑 `app/core/config.py`：

```python
# SQLite（默认）
DATABASE_URL = "sqlite:///./perf_calc.db"

# MySQL
DATABASE_URL = "mysql+pymysql://user:password@localhost/dbname"
```

### 启动脚本配置

如果 Python 路径不是 `D:\python38\python.exe`，请编辑 `启动.ps1`：

```powershell
$PYTHON = "你的Python路径"
```

## 常见问题

### 1. 端口被占用

```powershell
# 查找占用进程
netstat -ano | findstr :8001
netstat -ano | findstr :3000

# 停止进程
taskkill /PID <PID> /F
```

### 2. 依赖安装失败

```powershell
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 数据库错误

```powershell
# 重置数据库
Remove-Item perf_calc.db
alembic upgrade head
```

## 文档

详细文档请查看：
- [更新日志](文档/更新日志.md) - 最新功能和改进
- [启动指南](文档/启动指南.md) - 详细的启动说明
- [批次删除功能](文档/批次删除功能.md) - 批次删除使用说明
- [数据导入规则更新](文档/数据导入规则更新.md) - 导入规则说明
- [完整功能说明](文档/FULLSTACK_COMPLETION.md) - 系统功能详解
- [API 文档](http://localhost:8001/docs) - 在线 API 文档

## 许可证

MIT License

## 联系方式

如有问题，请联系开发团队。
