# 项目进度追踪（绩效核算系统 P0）

更新时间：2026-01-25

## 总览

- 目标：Sprint 1 后端可计算、可对账、可导出（FastAPI + MySQL/SQLite + SQLAlchemy + Alembic）
- 当前状态：Sprint 1 功能已实现并可本地运行，后端功能增强已完成

## 里程碑进度（PR 维度）

### PR1：项目骨架 + DB 结构 + 迁移 + seed

状态：✅ 已完成

- FastAPI 项目结构、Dockerfile、docker-compose
- SQLAlchemy 模型与 Alembic 迁移
- rule_param / item_mapping / item_behavior 默认 seed

### PR2：Excel 导入接口

状态：✅ 已完成

- POST /runs
- POST /runs/{id}/import/excel
- 月份括号解析、item_name 规范化
- 未映射项目写入 qc_issue

### PR3：计算引擎

状态：✅ 已完成

- DirectPay / Pool 归集 / Pool 分配 / 科室盈余
- fact_pay_detail / fact_pool / fact_pool_alloc / fact_pay_summary
- reconcile_item / qc_issue

### PR4：查询与导出接口

状态：✅ 已完成

- GET /runs/{id}/summary
- GET /runs/{id}/detail?name=
- GET /runs/{id}/reconcile
- GET /runs/{id}/qc
- GET /runs/{id}/export/excel（4 sheets）

### PR5：后端功能增强

状态：✅ 已完成（2026-01-21）

**新增功能**：

1. **规则参数管理 API**
   - GET/PUT /rule-params - 动态调整计算规则
   - 按类别分组展示参数
   - 批量更新支持

2. **项目映射管理增强**
   - 完整的 CRUD 接口
   - 批量操作支持
   - 项目行为配置管理

3. **数据校验增强**
   - 基础数据完整性验证
   - 人员数据一致性验证
   - 金额合理性验证
   - 业务规则验证

4. **批次管理增强**
   - 批次对比功能（月度对比）
   - 批次复制功能

5. **审计日志系统**
   - 操作日志记录
   - 审计追踪查询
   - 统计分析

**新增文件**：
- `app/schemas/rule.py` - 规则参数 Schema
- `app/api/routes/rule_params.py` - 规则参数路由
- `app/api/routes/audit.py` - 审计日志路由
- `app/calc/validator.py` - 数据校验模块
- `app/models/audit.py` - 审计日志模型
- `app/core/audit.py` - 审计日志工具
- `alembic/versions/0002_audit_log.py` - 审计日志表迁移
- `docs/BACKEND_ENHANCEMENT.md` - 后端增强文档

## 已完成工作清单

### Sprint 1 核心功能
- ✅ 数据模型与迁移：`alembic/versions/0001_init.py`
- ✅ 计算核心：`app/calc/engine.py`
- ✅ Excel 导入：`app/calc/importer.py`
- ✅ API 接口：`app/api/routes/runs.py` / `app/api/routes/mapping.py`
- ✅ README 启动与使用说明
- ✅ MySQL 迁移与 seed 已完成（Docker）
- ✅ 样本 Excel 全流程已验证并导出
- ✅ pytest 已通过（11 passed）

### 后端功能增强
- ✅ 规则参数管理 API（12个参数可动态配置）
- ✅ 项目映射完整 CRUD
- ✅ 项目行为管理（6种行为类型）
- ✅ 数据校验模块（4大类验证）
- ✅ 批次对比功能
- ✅ 批次复制功能
- ✅ 审计日志系统（6种操作类型）
- ✅ CORS 中间件配置
- ✅ 健康检查接口
- ✅ API 文档完善

## 当前运行状态

- ✅ 依赖已安装
- ✅ Docker MySQL 已启动（3307 → 3306）
- ✅ MySQL 已完成迁移与 seed
- ✅ FastAPI 已启动并监听 8000 端口
- ✅ 样本 Excel 全流程已跑通，导出文件：`run_2_export.xlsx`
- ✅ 后端功能增强已完成

## API 接口统计

### 批次管理（runs）
- POST /runs - 创建批次
- GET /runs - 批次列表
- POST /runs/{id}/lock - 锁定批次
- POST /runs/{id}/import/excel - 导入 Excel
- POST /runs/{id}/validate - 验证数据 ⭐新增
- POST /runs/{id}/calculate - 执行计算
- GET /runs/{id}/summary - 汇总结果
- GET /runs/{id}/detail - 明细查询
- GET /runs/{id}/reconcile - 对账表
- GET /runs/{id}/qc - 异常列表
- GET /runs/{id}/export/excel - 导出 Excel
- GET /runs/{id}/raw/{sheet} - 原始数据
- GET /runs/compare - 批次对比 ⭐新增
- POST /runs/{id}/copy - 复制批次 ⭐新增

### 项目映射（mappings）
- GET /mappings - 映射列表 ⭐新增
- GET /mappings/{id} - 单个映射 ⭐新增
- POST /mappings - 创建映射 ⭐新增
- PUT /mappings/{id} - 更新映射 ⭐新增
- DELETE /mappings/{id} - 删除映射 ⭐新增
- POST /mappings/batch - 批量创建 ⭐新增
- GET /mapping/unmatched - 未映射项目

### 项目行为（item-behaviors）
- GET /item-behaviors - 行为列表 ⭐新增
- GET /item-behaviors/{id} - 单个行为 ⭐新增
- POST /item-behaviors - 创建行为 ⭐新增
- PUT /item-behaviors/{id} - 更新行为 ⭐新增
- DELETE /item-behaviors/{id} - 删除行为 ⭐新增
- GET /item-behaviors/types/available - 可用类型 ⭐新增

### 规则参数（rule-params）⭐新增模块
- GET /rule-params - 参数列表
- GET /rule-params/{key} - 单个参数
- PUT /rule-params/{key} - 更新参数
- POST /rule-params/batch-update - 批量更新
- GET /rule-params/grouped/by-category - 按类别分组

### 审计日志（audit-logs）⭐新增模块
- GET /audit-logs - 日志列表
- GET /audit-logs/stats - 统计信息
- GET /audit-logs/types - 操作类型

### 系统接口
- GET / - API 根路径 ⭐新增
- GET /health - 健康检查 ⭐新增

**总计**：40+ 个 API 接口

## 待办事项（下一步）

### 短期优化（可选）
1. ⏳ 处理 pytest warnings（integration mark / openpyxl 时间警告）
2. ⏳ 清理 docker-compose `version` 字段警告
3. ⏳ 在关键接口中集成审计日志记录

### 中期规划（Sprint 2）
1. 🔲 前端界面开发（React + TypeScript）
2. 🔲 用户认证系统（JWT）
3. 🔲 角色权限管理
4. 🔲 报表系统（PDF 导出）
   - 目标/交付：在现有“批次（run）”维度基础上，提供可打印、可归档、可分享的 PDF 报表导出能力。
   - 范围（建议 v1）：首页封面 + 批次基本信息 + 汇总（summary）+ 对账表（reconcile）+ 异常清单（qc）；明细（detail）视体量可拆为“按人/按科室分页”或先不纳入 v1。
   - 现状：已支持 `GET /runs/{id}/export/excel`（4 sheets），数据侧具备 summary/reconcile/qc/detail 查询接口。
   - 方案对比：
     - A. 后端直接生成 PDF（如 ReportLab）：可控但排版开发成本高，维护难。
     - B. 后端生成 HTML + 渲染为 PDF（推荐：Jinja2 模板 + Headless Chromium/Playwright）：排版灵活、迭代快，但需要额外运行时依赖与容器镜像支持。
     - C. 前端渲染页面 + 浏览器“打印为 PDF”：最轻后端改动，但一致性/自动化归档较弱，且对用户操作依赖更强。
   - 决定：采用 B（HTML 模板 → PDF）：Jinja2 模板生成 HTML，由 Headless Chromium（建议 Playwright）渲染为 PDF；若线上环境对 Chromium 依赖敏感，则提供 C 作为兜底（导出 HTML + 浏览器打印为 PDF）。
   - 实施步骤（建议）：
     0) 准备运行时依赖：引入 Playwright（Python）并在 Docker/CI 中安装 Chromium 及其系统依赖；同步准备中文字体（容器内内置或挂载）。
     1) 定义报表结构与口径：每一页的字段、表格、排序、汇总口径，与现有 Excel 导出对齐（避免“同一批次多套口径”）。
     2) 新增导出接口：`GET /runs/{id}/export/pdf`（支持 query：`lang`、`paper=A4`、`orientation`、`sections=summary,reconcile,qc`）。
     3) 组装报表数据：复用现有查询服务（summary/reconcile/qc），统一 DTO，保证字段命名稳定。
     4) 模板与样式：引入 Jinja2 模板（封面/页眉页脚/分页/水印/页码），内置中文字体（或配置可挂载字体目录）。
     5) PDF 渲染与存储：渲染生成二进制流；可选落盘到 `exports/` 或对象存储；返回 `application/pdf` 并设置文件名（含 run_id、月份、生成时间）。
     6) 错误处理：批次不存在/未计算/数据为空/渲染失败给出明确错误码与提示。
   - 验证方式：
     - 功能：同一 run 导出 Excel 与 PDF 的关键汇总数字一致（抽样对比 summary/reconcile/qc）。
     - 版式：中文不乱码、分页正常、页眉页脚/页码正确；大数据量时不 OOM。
     - 自动化：新增接口的集成测试（至少验证 200、Content-Type、文件非空、关键字符串存在）。
   - 风险/阻塞点：
     - 字体与中文排版（容器内字体/字体授权）。
     - Headless Chromium 依赖（镜像体积、Linux 依赖、CI 环境一致性；以及部分受限环境下的沙箱/权限问题）。
     - 数据量大导致渲染慢（需做分段/分页策略与超时控制）。
5. 🔲 数据分析与可视化

## 技术债务

- 审计日志目前未自动记录操作人（需要集成用户系统）
- 部分接口缺少详细的错误处理
- 大数据量性能优化（异步计算）

## 风险与阻塞

- 无重大阻塞
- 本机 3306 端口被本地 MySQL 占用，Docker DB 已改用 3307

## 参考文档

- PRD: `docs/PRD.md`
- DB Schema: `docs/DB_SCHEMA.md`
- Calc Engine: `docs/CALC_ENGINE.md`
- API: `docs/API.md`
- Backend Enhancement: `docs/BACKEND_ENHANCEMENT.md` ⭐新增
- Sprint Plan: `docs/绩效核算系统 · Sprint 计划（P0）.md`

## 版本历史

- **v1.0.0** (2026-01-21 之前) - Sprint 1 核心功能完成
- **v1.1.0** (2026-01-21) - 后端功能增强完成
  - 规则参数管理
  - 项目映射增强
  - 数据校验增强
  - 批次对比与复制
  - 审计日志系统
