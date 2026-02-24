---
name: hospital-performance-calc
description: 用于医院科室绩效核算系统的批次执行与排障。用户出现以下中文诉求时优先触发：创建批次、导入Excel、编辑原始表、数据校验、执行绩效计算、查看汇总/明细/对账/QC、导出Excel或PDF、锁定或删除批次、调规则参数、维护项目映射和行为、查询未映射项目、批次对比/复制、查看审计日志。典型表达包括“跑一版绩效”“导入这个表算一下”“查为什么对账有差额”“调一下夜班费参数”“导出本月核算结果”。
---

# Hospital Performance Calc

## Overview

Use this skill to execute end-to-end accounting batches and configuration operations against the local FastAPI backend.
Default backend base URL is `http://localhost:8001`.

## Bootstrap

1. Confirm backend availability before changing data:
   - `Invoke-RestMethod -Uri "http://localhost:8001/health"`
2. Start services if needed:
   - `.\启动.ps1`
3. Use `samples/*.xlsx` for reproducible import tests.

## Run Lifecycle Workflow

1. Create a run:
```powershell
$base = "http://localhost:8001"
$run = Invoke-RestMethod -Method Post -Uri "$base/runs" -ContentType "application/json" -Body (@{
  month = "2026-01"
  dept_name = "内科"
  rule_version = "default"
} | ConvertTo-Json)
$runId = $run.run_id
```
2. Import Excel:
```powershell
Invoke-RestMethod -Method Post -Uri "$base/runs/$runId/import/excel?clear_existing=true" -Form @{
  file = Get-Item ".\samples\绩效核算模版.xlsx"
}
```
3. Validate before calculate:
```powershell
Invoke-RestMethod -Method Post -Uri "$base/runs/$runId/validate?save_to_qc=true"
```
4. Calculate:
```powershell
Invoke-RestMethod -Method Post -Uri "$base/runs/$runId/calculate"
```
5. Inspect outputs:
```powershell
Invoke-RestMethod -Uri "$base/runs/$runId/summary"
Invoke-RestMethod -Uri "$base/runs/$runId/reconcile"
Invoke-RestMethod -Uri "$base/runs/$runId/qc"
```
6. Export:
```powershell
Invoke-WebRequest -Uri "$base/runs/$runId/export/excel" -OutFile ".\run_$runId.xlsx"
Invoke-WebRequest -Uri "$base/runs/$runId/export/pdf?paper=A4&orientation=landscape&sections=summary,sign" -OutFile ".\run_$runId.pdf"
```
7. Lock or delete with care:
```powershell
Invoke-RestMethod -Method Post -Uri "$base/runs/$runId/lock"
# Destructive:
Invoke-RestMethod -Method Delete -Uri "$base/runs/$runId"
```

## Configuration And Governance Workflow

1. Manage rule parameters:
   - `GET /rule-params`
   - `PUT /rule-params/{param_key}`
   - `POST /rule-params/batch-update`
2. Manage mappings and behaviors:
   - `GET/POST/PUT/DELETE /mappings`
   - `GET/POST/PUT/DELETE /item-behaviors`
   - `GET /mapping/unmatched?run_id={run_id}`
3. Manage run operations:
   - `GET /runs/compare?run_id_1={a}&run_id_2={b}`
   - `POST /runs/{run_id}/copy?new_month=YYYY-MM`
4. Query audit logs:
   - `GET /audit-logs/`
   - `GET /audit-logs/stats`
   - `GET /audit-logs/types`

## Error Handling

1. Treat `400 Cannot calculate locked run` as immutable-run protection; use a new run.
2. Treat `404 Run not found` as stale `run_id`; list runs again via `GET /runs`.
3. Treat PDF `503` as missing Playwright Chromium runtime; run `python -m playwright install chromium`.
4. Re-run `validate` after any raw-sheet edit or mapping/rule change.

## References

Read `references/api-playbook.md` for endpoint matrix and request payload examples.
