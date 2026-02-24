

《接口设计（FastAPI）》
---------------

### 1. 批次

* `POST /runs`

* `GET /runs`

* `POST /runs/{id}/lock`

* * *

### 2. 导入 & 编辑

* `POST /runs/{id}/import/excel`

* `GET /runs/{id}/raw/{sheet}`

* `PUT /runs/{id}/raw/{sheet}`

* * *

### 3. 映射配置

* `GET /mapping/unmatched`

* `POST /mapping`

* `POST /item-behavior`

* * *

### 4. 计算

* `POST /runs/{id}/calculate`

* * *

### 5. 结果

* `GET /runs/{id}/summary`

* `GET /runs/{id}/detail?name=`

* `GET /runs/{id}/reconcile`

* `GET /runs/{id}/qc`

* `GET /runs/{id}/export/excel`

* * *
