# 🚀 快速启动指南

## 前置要求

- Python 3.11+
- MySQL 8.0+ 或 SQLite
- Git

---

## 方式一：本地启动（推荐用于开发）

### 1. 安装依赖

```bash
# 进入项目目录
cd "d:/我开发的项目/科室绩效核算v2"

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows PowerShell）
.\.venv\Scripts\Activate.ps1

# 或者（Windows CMD）
.venv\Scripts\activate.bat

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库

**选项 A: 使用 SQLite（最简单）**

默认配置已使用 SQLite，无需额外配置。

**选项 B: 使用 MySQL**

编辑 `app/core/config.py`，修改数据库连接：

```python
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/perf_calc"
```

### 3. 运行数据库迁移

```bash
# 升级到最新版本
alembic upgrade head

# 初始化种子数据
python -c "from app.core.db import SessionLocal; from app.core.seed import seed_defaults; db = SessionLocal(); seed_defaults(db); db.close()"
```

### 4. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 PowerShell 脚本
.\start.ps1
```

### 5. 访问 API 文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API 根路径: http://localhost:8000/

---

## 方式二：Docker 启动（推荐用于生产）

### 1. 启动服务

```bash
# 构建并启动
docker-compose up --build

# 后台运行
docker-compose up -d
```

### 2. 运行迁移

```bash
# 进入容器
docker-compose exec web bash

# 运行迁移
alembic upgrade head

# 初始化种子数据
python -c "from app.core.db import SessionLocal; from app.core.seed import seed_defaults; db = SessionLocal(); seed_defaults(db); db.close()"

# 退出容器
exit
```

### 3. 访问服务

- API: http://localhost:8000/docs

### 4. 停止服务

```bash
docker-compose down
```

---

## 快速测试

### 1. 测试健康检查

```bash
curl http://localhost:8000/health
```

预期输出：
```json
{"status": "healthy"}
```

### 2. 运行完整测试

```bash
# 运行单元测试
pytest -q

# 运行功能测试
python test_backend_enhancement.py
```

### 3. 测试完整流程

```bash
# 1. 创建批次
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d "{\"month\":\"2026-01\",\"dept_name\":\"内科\",\"rule_version\":\"default\"}"

# 2. 导入样本数据
curl -X POST http://localhost:8000/runs/1/import/excel \
  -F "file=@samples/绩效核算_最小测试样本.xlsx"

# 3. 验证数据
curl -X POST http://localhost:8000/runs/1/validate

# 4. 执行计算
curl -X POST http://localhost:8000/runs/1/calculate

# 5. 查看结果
curl http://localhost:8000/runs/1/summary

# 6. 导出 Excel
curl -O -J http://localhost:8000/runs/1/export/excel
```

---

## 常见问题

### Q1: 端口 8000 被占用

**解决方案**：修改启动端口

```bash
uvicorn app.main:app --reload --port 8001
```

### Q2: 数据库连接失败

**解决方案**：

1. 检查 MySQL 是否启动
2. 检查数据库连接配置
3. 尝试使用 SQLite（默认配置）

### Q3: 导入 Excel 失败

**解决方案**：

1. 检查 Excel 文件格式是否正确
2. 查看 `/runs/{id}/qc` 接口的异常信息
3. 参考 `samples/绩效核算模版.xlsx`

### Q4: 计算结果不正确

**解决方案**：

1. 运行数据验证：`POST /runs/{id}/validate`
2. 检查规则参数：`GET /rule-params/grouped/by-category`
3. 查看对账表：`GET /runs/{id}/reconcile`
4. 查看异常列表：`GET /runs/{id}/qc`

---

## 开发工具推荐

### API 测试
- **Swagger UI**: http://localhost:8000/docs（内置）
- **Postman**: 导入 OpenAPI 规范
- **curl**: 命令行测试

### 数据库管理
- **DBeaver**: 通用数据库工具
- **MySQL Workbench**: MySQL 专用
- **DB Browser for SQLite**: SQLite 专用

### 代码编辑
- **VS Code**: 推荐插件
  - Python
  - Pylance
  - SQLTools
  - REST Client

---

## 项目结构说明

```
科室绩效核算v2/
├── app/                      # 应用代码
│   ├── api/                  # API 路由
│   │   └── routes/           # 路由模块
│   │       ├── runs.py       # 批次管理
│   │       ├── mapping.py    # 项目映射
│   │       ├── rule_params.py # 规则参数
│   │       └── audit.py      # 审计日志
│   ├── calc/                 # 计算引擎
│   │   ├── engine.py         # 核心计算逻辑
│   │   ├── importer.py       # Excel 导入
│   │   ├── validator.py      # 数据验证
│   │   └── utils.py          # 工具函数
│   ├── core/                 # 核心配置
│   │   ├── config.py         # 配置文件
│   │   ├── db.py             # 数据库连接
│   │   ├── seed.py           # 种子数据
│   │   └── audit.py          # 审计工具
│   ├── models/               # 数据模型
│   │   ├── models.py         # 业务模型
│   │   └── audit.py          # 审计模型
│   ├── schemas/              # Pydantic 模型
│   │   ├── run.py            # 批次相关
│   │   └── rule.py           # 规则相关
│   └── main.py               # 应用入口
├── alembic/                  # 数据库迁移
│   └── versions/             # 迁移脚本
├── docs/                     # 文档
├── samples/                  # 测试样本
├── tests/                    # 测试用例
├── requirements.txt          # 依赖列表
├── alembic.ini               # Alembic 配置
├── docker-compose.yml        # Docker 配置
└── README.md                 # 项目说明
```

---

## 下一步

### 学习资源
1. 阅读 [API 文档](API.md)
2. 查看 [计算引擎说明](CALC_ENGINE.md)
3. 了解 [数据库设计](DB_SCHEMA.md)
4. 阅读 [后端增强文档](BACKEND_ENHANCEMENT.md)

### 开发建议
1. 熟悉 API 接口（访问 Swagger UI）
2. 运行测试脚本了解功能
3. 查看样本数据理解业务
4. 阅读代码注释理解实现

### 获取帮助
- 查看文档：`docs/` 目录
- 运行测试：`pytest -v`
- 查看日志：检查控制台输出
- API 文档：http://localhost:8000/docs

---

## 🎉 开始使用

现在您可以：

1. ✅ 启动服务
2. ✅ 导入数据
3. ✅ 执行计算
4. ✅ 查看结果
5. ✅ 导出报表

**祝您使用愉快！** 🚀
