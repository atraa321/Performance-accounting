# 停止所有服务

Write-Host "停止服务..." -ForegroundColor Yellow

# 停止 Python 进程
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*python*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# 停止 Node 进程
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# 清理 Job
Get-Job | Stop-Job -ErrorAction SilentlyContinue
Get-Job | Remove-Job -ErrorAction SilentlyContinue

Write-Host "服务已停止" -ForegroundColor Green
