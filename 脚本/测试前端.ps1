# 测试前端启动

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试前端启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Node.js
Write-Host "[1/3] 检查 Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
    Write-Host "✓ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 未找到 Node.js" -ForegroundColor Red
    exit 1
}

# 检查前端目录
Write-Host ""
Write-Host "[2/3] 检查前端目录..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    Write-Host "✓ 前端目录存在" -ForegroundColor Green
} else {
    Write-Host "✗ 未找到前端目录" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host ""
Write-Host "[3/3] 检查依赖..." -ForegroundColor Yellow
if (Test-Path "frontend\node_modules") {
    Write-Host "✓ 依赖已安装" -ForegroundColor Green
} else {
    Write-Host "安装依赖..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
    Write-Host "✓ 依赖安装完成" -ForegroundColor Green
}

# 启动前端
Write-Host ""
Write-Host "启动前端..." -ForegroundColor Yellow
Write-Host "端口: 3000" -ForegroundColor Cyan
Write-Host "代理: http://localhost:8001" -ForegroundColor Cyan
Write-Host ""

$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD\frontend
    npm run dev
}

Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ 前端启动成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  前端: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  前端运行中..." -ForegroundColor Cyan
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
