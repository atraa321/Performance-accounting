

《绩效计算引擎设计》
----------

### 1. 总体 Pipeline

    导入 → 校验 → 映射 → DirectPay
         → Pool归集 → Pool分配
         → 科室盈余
         → 汇总 → 对账 → 异常

* * *

### 2. DirectPay 项目公式（示例）

#### 医师夜班

    单价 = 医师夜班费 / 医师夜班总数
    个人 = 单价 × 个人夜班数

#### 护理夜班

同上

* * *

### 3. 护理池分配

    AvgScore = avg(score > 0)
    护士长分数 = AvgScore × 1.4
    
    个人金额 = NursingPool × 权重 / Σ权重

* * *

### 4. 医师汇总分配

    if workload > 0:
      weight = workload
    else:
      weight = 0.8
    
    个人金额 = DoctorPool × weight / Σweight

* * *

### 5. 科室盈余

    主任 = 15%
    护士长 = 5%
    剩余 = 80%
    
    剩余按绩效分数权重
    排除进修/产假/请假

* * *

### 6. ReconOnly 项目（如手术室成本）

    allocated_amount = 0
    delta = source_amount
    仅进入对账表

* * *

### 7. 统一尾差处理

* round 到分

* 差额加到“最大权重者”

* * *
