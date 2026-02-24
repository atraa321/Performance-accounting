

《数据库设计（MySQL，P0）》
-----------------

> 设计原则：**所有计算可追溯、可复算、可对账**

### 1. 批次与规则

* `run_batch`

* `rule_set`

* `rule_param`

（字段略，按你上一条确认的版本）

* * *

### 2. Raw 输入表

* `raw_hospital_perf_item`

* `raw_roster`

* `raw_night_shift`

* `raw_reading_fee`

* `raw_doctor_workload`

* `raw_nurse_workload`

* `raw_manual_doctor_workload_pay`

* `raw_manual_pool_adjust`

* * *

### 3. 项目映射与行为

    dict_item_mapping(
      raw_item_name,
      item_code,
      priority
    )
    
    dict_item_behavior(
      item_code,
      behavior_type -- DIRECT / POOL_NURSING / POOL_DOCTOR / MANUAL / RECON_ONLY / SPECIAL
    )

* * *

### 4. 计算结果

* `fact_pay_detail`（**所有发钱明细唯一来源**）

* `fact_pool`

* `fact_pool_alloc`

* `fact_pay_summary`

* * *

### 5. 对账与异常

* `reconcile_item`

* `qc_issue`

* * * 
