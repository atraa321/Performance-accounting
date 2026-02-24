# 后端功能增强文档

更新时间：2026-01-21

## 新增功能概览

本次后端增强主要增加了以下功能模块：

### 1. 规则参数管理 API ✅

**路由前缀**: `/rule-params`

**功能说明**: 允许用户通过 API 动态调整计算规则参数，无需修改代码

**接口列表**:

- `GET /rule-params` - 获取所有规则参数
- `GET /rule-params/{param_key}` - 获取单个规则参数
- `PUT /rule-params/{param_key}` - 更新单个规则参数
- `POST /rule-params/batch-update` - 批量更新规则参数
- `GET /rule-params/grouped/by-category` - 按类别分组获取参数（便于前端展示）

**支持的参数类别**:
- 判读费分配（化验判读费医师/护理比例、科主任判读费分配比例）
- 床补分配（医师/护理池比例）
- 护理池分配（护士长分数系数）
- 医师池分配（最小权重）
- 科室盈余分配（主任/护士长比例）
- 其他（住院证单价等）

**使用示例**:

```bash
# 获取所有参数
curl http://localhost:8000/rule-params

# 更新单个参数
curl -X PUT http://localhost:8000/rule-params/lab_doctor_ratio \
  -H "Content-Type: application/json" \
  -d '{"param_value": "0.75", "param_value_num": 0.75, "param_desc": "化验判读费医师比例"}'

# 按类别获取参数
curl http://localhost:8000/rule-params/grouped/by-category
```

---

### 2. 项目映射管理增强 ✅

**路由前缀**: `/mappings`, `/item-behaviors`

**功能说明**: 完善的项目映射和行为配置管理

**接口列表**:

**项目映射**:
- `GET /mappings` - 获取所有项目映射（支持按 is_active 过滤）
- `GET /mappings/{mapping_id}` - 获取单个映射
- `POST /mappings` - 创建项目映射
- `PUT /mappings/{mapping_id}` - 更新项目映射
- `DELETE /mappings/{mapping_id}` - 删除项目映射（软删除）
- `POST /mappings/batch` - 批量创建映射
- `GET /mapping/unmatched` - 获取未映射的项目（支持按 run_id 过滤）

**项目行为**:
- `GET /item-behaviors` - 获取所有项目行为
- `GET /item-behaviors/{behavior_id}` - 获取单个行为
- `POST /item-behaviors` - 创建项目行为
- `PUT /item-behaviors/{behavior_id}` - 更新项目行为
- `DELETE /item-behaviors/{behavior_id}` - 删除项目行为
- `GET /item-behaviors/types/available` - 获取可用的行为类型

**行为类型**:
- `DIRECT` - 直接发放
- `POOL_NURSING` - 护理池
- `POOL_DOCTOR` - 医师池
- `SPECIAL` - 特殊规则
- `RECON_ONLY` - 仅对账
- `UNCLASSIFIED` - 未分类

---

### 3. 数据校验增强 ✅

**模块**: `app/calc/validator.py`

**功能说明**: 在导入和计算前进行全面的业务规则校验

**校验内容**:

1. **基础数据完整性**
   - 检查是否有院发绩效表数据
   - 检查是否有发放名单
   - 检查金额是否有负数

2. **人员数据一致性**
   - 夜班统计中的人员是否在发放名单中
   - 医师工作量中的人员是否在发放名单中
   - 护士工作量中的人员是否在发放名单中
   - 识别判读费中的外部医师

3. **金额合理性**
   - 绩效分数是否为负数或异常高
   - 夜班数是否为负数或超过31天

4. **业务规则**
   - 检查是否有科主任
   - 检查是否有护士长
   - 统计医师和护士的比例

**API 接口**:
- `POST /runs/{run_id}/validate` - 验证 run 数据

**使用示例**:

```bash
# 验证数据并保存到 QC 表
curl -X POST http://localhost:8000/runs/1/validate?save_to_qc=true
```

**返回示例**:

```json
{
  "is_valid": true,
  "error_count": 0,
  "warning_count": 2,
  "info_count": 3,
  "errors": [],
  "warnings": [
    {
      "message": "夜班统计中的人员 '张三' 不在发放名单中",
      "issue_type": "EMPLOYEE_NOT_IN_ROSTER",
      "name": "张三",
      "source": "夜班统计"
    }
  ],
  "info": [
    {
      "message": "院发绩效表共 15 条记录",
      "issue_type": "INFO"
    }
  ]
}
```

---

### 4. 批次管理增强 ✅

**新增接口**:

- `GET /runs/compare?run_id_1={id1}&run_id_2={id2}` - 对比两个批次的计算结果
- `POST /runs/{run_id}/copy` - 复制批次（仅复制配置，不复制数据）

**批次对比功能**:
- 对比两个月份的绩效发放金额
- 显示每个人的金额变化和变化百分比
- 统计共同人员、仅在某个批次中的人员

**使用示例**:

```bash
# 对比两个批次
curl "http://localhost:8000/runs/compare?run_id_1=1&run_id_2=2"

# 复制批次
curl -X POST http://localhost:8000/runs/1/copy \
  -H "Content-Type: application/json" \
  -d '{"new_month": "2026-02"}'
```

---

### 5. 审计日志系统 ✅

**模块**: `app/models/audit.py`, `app/core/audit.py`, `app/api/routes/audit.py`

**功能说明**: 记录所有关键操作，支持审计追踪

**记录的操作类型**:
- `RUN_MANAGEMENT` - 批次管理（创建、锁定）
- `DATA_IMPORT` - 数据导入
- `CALCULATION` - 绩效计算
- `CONFIG_CHANGE` - 配置变更（规则参数、项目映射）
- `DATA_EXPORT` - 数据导出
- `DATA_VALIDATION` - 数据验证

**API 接口**:
- `GET /audit-logs` - 获取审计日志列表（支持多种过滤条件）
- `GET /audit-logs/stats` - 获取审计统计信息
- `GET /audit-logs/types` - 获取所有操作类型

**查询参数**:
- `run_id` - 按批次过滤
- `operation_type` - 按操作类型过滤
- `status` - 按状态过滤（SUCCESS/FAILED）
- `operator` - 按操作人过滤
- `start_date` / `end_date` - 按时间范围过滤
- `limit` / `offset` - 分页

**使用示例**:

```bash
# 获取最近100条日志
curl http://localhost:8000/audit-logs?limit=100

# 获取某个批次的所有操作
curl http://localhost:8000/audit-logs?run_id=1

# 获取最近7天的统计
curl http://localhost:8000/audit-logs/stats?days=7
```

**数据库迁移**:
需要运行新的迁移文件：

```bash
alembic upgrade head
```

---

## 数据库变更

### 新增表

**operation_log** - 操作日志表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| run_id | Integer | 关联的批次ID |
| operation_type | String(50) | 操作类型 |
| operation_name | String(200) | 操作名称 |
| operator | String(100) | 操作人 |
| details | Text | 操作详情 |
| payload | JSON | 操作数据 |
| status | String(20) | 状态（SUCCESS/FAILED） |
| error_message | Text | 错误信息 |
| created_at | DateTime | 操作时间 |
| ip_address | String(50) | IP地址 |
| user_agent | String(500) | 用户代理 |

**索引**:
- `idx_operation_log_run_id` - run_id 索引
- `idx_operation_log_type` - operation_type 索引
- `idx_operation_log_created_at` - created_at 索引

---

## 新增文件清单

```
app/
├── schemas/
│   └── rule.py                    # 规则参数和映射的 Pydantic 模型
├── api/
│   └── routes/
│       ├── rule_params.py         # 规则参数管理路由
│       └── audit.py               # 审计日志路由
├── calc/
│   └── validator.py               # 数据校验模块
├── models/
│   └── audit.py                   # 审计日志模型
└── core/
    └── audit.py                   # 审计日志工具类

alembic/
└── versions/
    └── 0002_audit_log.py          # 审计日志表迁移文件
```

---

## 使用流程

### 1. 运行数据库迁移

```bash
cd "d:/我开发的项目/科室绩效核算v2"
alembic upgrade head
```

### 2. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问 API 文档

打开浏览器访问：`http://localhost:8000/docs`

### 4. 完整工作流程

```bash
# 1. 创建批次
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"month":"2026-01","dept_name":"内科","rule_version":"default"}'

# 2. 导入 Excel
curl -X POST http://localhost:8000/runs/1/import/excel \
  -F "file=@samples/绩效核算_最小测试样本.xlsx"

# 3. 验证数据
curl -X POST http://localhost:8000/runs/1/validate

# 4. 查看未映射项目
curl http://localhost:8000/mapping/unmatched?run_id=1

# 5. 配置项目映射（如果需要）
curl -X POST http://localhost:8000/mappings \
  -H "Content-Type: application/json" \
  -d '{"raw_item_name":"新项目","item_code":"NEW_ITEM","priority":100}'

# 6. 调整规则参数（如果需要）
curl -X PUT http://localhost:8000/rule-params/lab_doctor_ratio \
  -H "Content-Type: application/json" \
  -d '{"param_value":"0.75","param_value_num":0.75}'

# 7. 执行计算
curl -X POST http://localhost:8000/runs/1/calculate

# 8. 查看结果
curl http://localhost:8000/runs/1/summary

# 9. 导出 Excel
curl -O -J http://localhost:8000/runs/1/export/excel

# 10. 查看审计日志
curl http://localhost:8000/audit-logs?run_id=1
```

---

## 后续建议

### 短期优化（1-2周）

1. **用户认证系统**
   - 集成 JWT 认证
   - 用户角色权限管理
   - 审计日志自动记录操作人

2. **数据导入优化**
   - 支持更多 Excel 格式
   - 导入进度反馈
   - 导入失败回滚

3. **计算性能优化**
   - 大数据量批处理
   - 异步计算任务
   - 计算进度查询

### 中期优化（1-2月）

1. **前端界面开发**
   - React + TypeScript + Ant Design
   - 可视化配置界面
   - 图表展示

2. **报表系统**
   - 自定义报表模板
   - PDF 导出
   - 邮件发送

3. **数据分析**
   - 月度趋势分析
   - 人员绩效对比
   - 异常检测

---

## 技术栈

- **框架**: FastAPI 0.110.0
- **数据库**: MySQL 8.0 / SQLite
- **ORM**: SQLAlchemy 2.0.27
- **迁移**: Alembic 1.13.1
- **Excel**: openpyxl 3.1.2
- **验证**: Pydantic 2.6.1

---

## 联系与支持

如有问题或建议，请查看项目文档或提交 Issue。
