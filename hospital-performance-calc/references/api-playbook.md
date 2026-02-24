# API Playbook

## Service

- Base URL: `http://localhost:8001`
- Health check: `GET /health`
- API docs: `GET /docs`

## Run Lifecycle Endpoints

1. Create run: `POST /runs`
```json
{
  "month": "2026-01",
  "dept_name": "内科",
  "rule_version": "default"
}
```
2. List runs: `GET /runs`
3. Lock run: `POST /runs/{run_id}/lock`
4. Delete run: `DELETE /runs/{run_id}` (blocked when run is locked)

## Import And Data Edit Endpoints

1. Import all sheets from Excel:
   - `POST /runs/{run_id}/import/excel?clear_existing=true`
   - form field: `file=<xlsx>`
2. Import one sheet:
   - `POST /runs/{run_id}/import/excel/sheet?sheet={sheet}`
3. Query raw sheet:
   - `GET /runs/{run_id}/raw/{sheet}`
4. Replace raw sheet rows:
   - `POST /runs/{run_id}/raw/{sheet}`
```json
{
  "rows": []
}
```
5. Supported `sheet` keys:
   - `hospital_perf_item`
   - `roster`
   - `night_shift`
   - `reading_fee`
   - `doctor_workload`
   - `nurse_workload`
   - `manual_doctor_workload_pay`

## Validation, Calculation, And Results

1. Validate run:
   - `POST /runs/{run_id}/validate?save_to_qc=true`
2. Calculate run:
   - `POST /runs/{run_id}/calculate`
3. Summary:
   - `GET /runs/{run_id}/summary`
4. Detail:
   - `GET /runs/{run_id}/detail`
   - `GET /runs/{run_id}/detail?name={person_name}`
5. Reconcile:
   - `GET /runs/{run_id}/reconcile`
6. QC issues:
   - `GET /runs/{run_id}/qc`
7. Export:
   - `GET /runs/{run_id}/export/excel`
   - `GET /runs/{run_id}/export/pdf?paper=A4&orientation=landscape&sections=summary,sign`
   - `GET /runs/{run_id}/export/html?paper=A4&orientation=landscape&sections=summary,reconcile,qc,sign`

## Manual Adjustment Endpoints

1. Manual doctor workload pay:
   - `GET /runs/{run_id}/manual/workload`
   - `POST /runs/{run_id}/manual/workload`
```json
{
  "rows": [
    { "name": "张三", "amount": 1200.0 }
  ]
}
```
2. Study-leave subsidy:
   - `GET /runs/{run_id}/manual/study-leave`
   - `POST /runs/{run_id}/manual/study-leave`
3. Generic manual entries:
   - `GET /runs/{run_id}/manual/entries`
   - `POST /runs/{run_id}/manual/entries`
```json
{
  "rows": [
    {
      "target_type": "PERSON",
      "target_value": "张三",
      "item_type": "OTHER",
      "amount": 500.0
    }
  ]
}
```
4. Manual allocatable list:
   - `GET /runs/{run_id}/manual/allocatable`

## Configuration Endpoints

1. Rule params:
   - `GET /rule-params`
   - `GET /rule-params/{param_key}`
   - `PUT /rule-params/{param_key}`
   - `POST /rule-params/batch-update`
   - `GET /rule-params/grouped/by-category`
2. Item mappings:
   - `GET /mappings`
   - `GET /mappings/{mapping_id}`
   - `POST /mappings`
   - `PUT /mappings/{mapping_id}`
   - `DELETE /mappings/{mapping_id}` (soft delete to inactive)
   - `POST /mappings/batch`
   - `GET /mapping/unmatched?run_id={run_id}`
3. Item behaviors:
   - `GET /item-behaviors`
   - `GET /item-behaviors/{behavior_id}`
   - `POST /item-behaviors`
   - `PUT /item-behaviors/{behavior_id}`
   - `DELETE /item-behaviors/{behavior_id}`
   - `GET /item-behaviors/types/available`

## Analysis And Audit Endpoints

1. Compare runs:
   - `GET /runs/compare?run_id_1={a}&run_id_2={b}`
2. Copy run config:
   - `POST /runs/{run_id}/copy?new_month=YYYY-MM`
3. Audit logs:
   - `GET /audit-logs/?limit=100&offset=0`
   - `GET /audit-logs/stats?days=7`
   - `GET /audit-logs/types`
