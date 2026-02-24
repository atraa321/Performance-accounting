# 完整测试脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  系统启动测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查后端
Write-Host "[1/2] 检查后端服务..." -ForegroundColor Yellow
$backendPort = netstat -ano | findstr :8001
if ($backendPort) {
    Write-Host "✓ 后端服务运行中 (端口 8001)" -ForegroundColor Green
    
    # 测试健康检查
    try {
        $response = curl.exe -s http://localhost:8001/health
        Write-Host "✓ 健康检查通过" -ForegroundColor Green
        Write-Host "  响应: $response" -ForegroundColor Gray
    } catch {
        Write-Host "⚠ 健康检查失败" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ 后端服务未运行" -ForegroundColor Red
}

# 2. 检查前端
Write-Host ""
Write-Host "[2/2] 检查前端服务..." -ForegroundColor Yellow
$frontendPort = netstat -ano | findstr :3000
if ($frontendPort) {
    Write-Host "✓ 前端服务运行中 (端口 3000)" -ForegroundColor Green
} else {
    Write-Host "✗ 前端服务未运行" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试结果" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($backendPort -and $frontendPort) {
    Write-Host "✓ 所有服务运行正常" -ForegroundColor Green
    Write-Host ""
    Write-Host "访问地址:" -ForegroundColor Cyan
    Write-Host "  前端: http://localhost:3000" -ForegroundColor White
    Write-Host "  后端: http://localhost:8001" -ForegroundColor White
    Write-Host "  文档: http://localhost:8001/docs" -ForegroundColor White
} elseif ($backendPort) {
    Write-Host "⚠ 后端运行正常，前端未启动" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "启动前端:" -ForegroundColor Cyan
    Write-Host "  .\测试前端.ps1" -ForegroundColor White
} elseif ($frontendPort) {
    Write-Host "⚠ 前端运行正常，后端未启动" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "启动后端:" -ForegroundColor Cyan
    Write-Host "  .\测试后端.ps1" -ForegroundColor White
} else {
    Write-Host "✗ 所有服务未运行" -ForegroundColor Red
    Write-Host ""
    Write-Host "启动系统:" -ForegroundColor Cyan
    Write-Host "  .\启动.ps1" -ForegroundColor White
}

Write-Host ""
