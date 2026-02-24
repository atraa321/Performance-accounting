# 测试后端启动

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试后端启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PYTHON = "D:\python38\python.exe"

# 检查 Python
Write-Host "[1/4] 检查 Python..." -ForegroundColor Yellow
if (Test-Path $PYTHON) {
    $version = & $PYTHON --version
    Write-Host "✓ $version" -ForegroundColor Green
} else {
    Write-Host "✗ 未找到 Python" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host ""
Write-Host "[2/4] 检查依赖..." -ForegroundColor Yellow
try {
    & $PYTHON -c "import fastapi, uvicorn, sqlalchemy, alembic; print('✓ 所有依赖已安装')"
} catch {
    Write-Host "✗ 依赖检查失败" -ForegroundColor Red
    exit 1
}

# 检查数据库
Write-Host ""
Write-Host "[3/4] 检查数据库..." -ForegroundColor Yellow
if (Test-Path "perf_calc.db") {
    Write-Host "✓ 数据库已存在" -ForegroundColor Green
} else {
    Write-Host "初始化数据库..." -ForegroundColor Yellow
    & $PYTHON -m alembic upgrade head
    Write-Host "✓ 数据库初始化完成" -ForegroundColor Green
}

# 启动后端
Write-Host ""
Write-Host "[4/4] 启动后端..." -ForegroundColor Yellow
Write-Host "端口: 8001" -ForegroundColor Cyan
Write-Host ""

$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & $using:PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8001
}

Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 测试连接
$maxRetries = 10
$retryCount = 0
$success = $false

while ($retryCount -lt $maxRetries -and -not $success) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $success = $true
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  ✓ 后端启动成功！" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "访问地址:" -ForegroundColor Cyan
            Write-Host "  API: http://localhost:8001" -ForegroundColor White
            Write-Host "  文档: http://localhost:8001/docs" -ForegroundColor White
            Write-Host ""
            Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
            Write-Host ""
        }
    } catch {
        $retryCount++
        Write-Host "  尝试 $retryCount/$maxRetries..." -ForegroundColor Gray
        Start-Sleep -Seconds 1
    }
}

if (-not $success) {
    Write-Host ""
    Write-Host "✗ 后端启动失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "错误信息:" -ForegroundColor Yellow
    Receive-Job $job
    Stop-Job $job
    Remove-Job $job
    exit 1
}

# 测试 API
Write-Host "测试 API 端点..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/docs" -TimeoutSec 2
    Write-Host "✓ API 文档可访问" -ForegroundColor Green
} catch {
    Write-Host "✗ API 文档访问失败" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  后端运行中..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 保持运行
try {
    while ($true) {
        $state = Get-Job -Id $job.Id | Select-Object -ExpandProperty State
        if ($state -ne "Running") {
            Write-Host "✗ 服务已停止" -ForegroundColor Red
            Receive-Job $job
            break
        }
        Start-Sleep -Seconds 5
    }
} finally {
    Stop-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -ErrorAction SilentlyContinue
    Write-Host "服务已停止" -ForegroundColor Yellow
}
