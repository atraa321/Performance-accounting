

绩效核算系统 · Sprint 计划（P0）
======================

总体节奏（建议）
--------

* **Sprint 1（基础可跑）**：数据能进、规则能算、结果能出

* **Sprint 2（可用可交付）**：可视化、对账、异常、导出、锁定

> 每个 Sprint 都是**独立可验收**的，不会出现“全做完才能用”。

* * *

🟦 Sprint 1（核心计算引擎 + 数据通路）
==========================

**目标**：  
👉 导入 Excel → 映射项目 → 计算所有 DirectPay + Pool → 生成“数据版汇总表”

### Sprint 1 交付定义

* 后端可一键计算

* 数据库结构完整

* 所有你已定规则 **100%生效**

* 用 Postman / Swagger 就能跑通整月绩效

* * *

Sprint 1 · Backlog（P0 必做）
-------------------------

### 1️⃣ 项目初始化 & 基础架构

* FastAPI 项目初始化

* MySQL 连接 & ORM（SQLAlchemy）

* 项目模块结构（import / calc / pool / report / qc）

* * *

### 2️⃣ 数据库建表（按 DB_SCHEMA.md）

* run_batch

* rule_set / rule_param

* dict_item_mapping

* dict_item_behavior

* 所有 raw_* 表

* dim_employee_month

* fact_pay_detail

* fact_pool / fact_pool_alloc

* fact_pay_summary

* reconcile_item

* qc_issue

**验收点**：  
👉 新建 run_id 后，所有 raw 表可插入数据

* * *

### 3️⃣ Excel 导入（后端）

* 解析 Excel（openpyxl / pandas）

* Sheet → raw_* 表映射

* 括号月份解析（如 `(11月)`）

* 金额/数值基础校验

* 记录 row_no + sheet_name

**验收点**：  
👉 上传你现在这份绩效 Excel，所有表能完整入库

* * *

### 4️⃣ 项目名 → item_code 映射引擎

* normalize_item_name（去空格/括号）

* 精确 / 关键词匹配

* 未映射项目 → `UNCLASSIFIED_ITEM`

* 写入 qc_issue：`ITEM_MAPPING_MISSING`

**验收点**：  
👉 你这份院发绩效表，已知项目全部自动映射成功

* * *

### 5️⃣ 生成人员主数据 dim_employee_month

* 从绩效发放名单生成

* 角色识别（doctor / nurse / chief / headnurse）

* external 医师标记（判读费出现但名单无）

* eligible_for_surplus_weight 默认=true

* * *

### 6️⃣ 夜班拆分（合表按岗位）

* raw_night_shift → resolved_group

* unknown 行写 qc_issue

* 医师/护理夜班分别统计

* * *

### 7️⃣ DirectPay 计算（核心）

* 医师夜班

* 护理夜班

* 判读费（化验70/30）

* 科主任判读费（80/0/20）

* 床补（2/3医师）

* 住院证补贴（*50 + 结余）

* 抽血费

* 医师手动工作量

👉 全部写入 `fact_pay_detail`

* * *

### 8️⃣ Pool 归集

* NursingPool 归集（6项）

* DoctorPool 归集（胰岛素泵 + 手动）

* 写入 fact_pool

* * *

### 9️⃣ Pool 出池分配

* 护理池：分数权重 + 护士长 avg×1.4 + 0分排除

* 医师池：工作量 / 0.8

* 尾差处理

* 写入 fact_pool_alloc + fact_pay_detail

* * *

### 🔟 科室盈余（Special）

* 主任15%

* 护士长5%

* 剩余按绩效分数

* 排除进修/产假/请假（先按默认）

* * *

### 1️⃣1️⃣ 汇总表生成

* fact_pay_detail → fact_pay_summary

* direct_total / pool_total / grand_total

* * *

### ✅ Sprint 1 验收标准

* 给定你当前 Excel

* **能算出每个人的“本月应发合计”**

* **所有规则与口径与你描述一致**

* 不要求 UI，只要接口 + DB 正确

* * *

🟩 Sprint 2（可视化 + 对账 + 交付）
==========================

**目标**：  
👉 不写 SQL 也能用，财务/科室能看懂、能对账、能导出

* * *

Sprint 2 · Backlog（P0 可交付）
--------------------------

### 1️⃣ 前端基础页面

* 核算批次列表

* 新建核算（月度）

* * *

### 2️⃣ Excel 导入 + 预览

* 上传 Excel

* Sheet 表格预览（可滚动）

* 红色高亮异常行

* 支持行级编辑 & 保存

* * *

### 3️⃣ 项目映射 & 行为配置页（非常关键）

* 未映射项目列表

* 选择 item_code

* 选择行为（入护理池 / 医师池 / 手动 / 只对账）

* 保存后自动复用

* * *

### 4️⃣ 人员标记配置

* 勾选：是否参与科室盈余权重

* 夜班 unknown 行手动指定岗位

* 外部医师确认

* * *

### 5️⃣ 计算与进度反馈

* 点击【计算】

* Loading / 成功 / 错误提示

* 防重复计算

* * *

### 6️⃣ 结果展示

* 汇总表（按人）

* 岗位筛选（医师/护理）

* 点击姓名 → 明细钻取（pay_code）

* * *

### 7️⃣ 对账与异常

* 对账表（来源金额 vs 分配）

* ReconOnly 项目标注说明

* 异常列表（可导出）

* * *

### 8️⃣ Excel 导出

* 汇总表

* 明细表

* 对账表

* 异常清单

* * *

### 9️⃣ 锁定与回看

* 锁定 run（只读）

* 历史月份查询

* * *

### ✅ Sprint 2 验收标准

* 不懂技术的人也能操作

* 财务能对账

* 可直接导出发放依据

* 支持月度留痕

* * *
