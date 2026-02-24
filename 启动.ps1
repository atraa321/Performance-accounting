# 绩效核算系统 - 启动脚本（改进版）

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  绩效核算系统启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设定脚本根目录，避免从其他路径执行导致找不到模块
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

# Python 路径（自动探测，优先项目环境）
function Test-PythonExecutable([string]$CandidatePath) {
    if (-not $CandidatePath) { return $null }
    if (-not (Test-Path $CandidatePath)) { return $null }
    $ver = & $CandidatePath --version 2>$null
    if ($LASTEXITCODE -eq 0) { return $ver }
    return $null
}

function Test-PortAvailable([int]$Port) {
    # 先排除已监听端口，避免误判
    $listening = netstat -ano | findstr ":$Port" | findstr "LISTENING"
    if ($listening) { return $false }

    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Server.ExclusiveAddressUse = $true
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

$PYTHON = $null
$PYTHON_VERSION = $null

$pythonCandidates = @(
    (Join-Path $Root ".venv\Scripts\python.exe"),
    "D:\python312\python.exe",
    "C:\Users\庄主\AppData\Local\Programs\Python\Python312\python.exe"
)

foreach ($candidate in $pythonCandidates) {
    $candidateVersion = Test-PythonExecutable $candidate
    if ($candidateVersion) {
        $PYTHON = $candidate
        $PYTHON_VERSION = $candidateVersion
        break
    }
}

if (-not $PYTHON) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd -and $pythonCmd.Source) {
        $candidateVersion = Test-PythonExecutable $pythonCmd.Source
        if ($candidateVersion) {
            $PYTHON = $pythonCmd.Source
            $PYTHON_VERSION = $candidateVersion
        }
    }
}

if (-not $PYTHON) {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        try {
            $launcherPath = (& py -3.12 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1).Trim()
            $candidateVersion = Test-PythonExecutable $launcherPath
            if ($candidateVersion) {
                $PYTHON = $launcherPath
                $PYTHON_VERSION = $candidateVersion
            }
        } catch {}
    }
}

# 1. 检查 Python
Write-Host "[1/5] 检查 Python..." -ForegroundColor Yellow
if (-not $PYTHON) {
    Write-Host "✗ 未找到可用的 Python 3.12 解释器" -ForegroundColor Red
    Write-Host "请安装 Python 3.12，或将 python.exe 加入 PATH" -ForegroundColor Yellow
    pause
    exit 1
}
if (-not $PYTHON_VERSION) {
    $PYTHON_VERSION = & $PYTHON --version
}
Write-Host "✓ $PYTHON_VERSION ($PYTHON)" -ForegroundColor Green

# 后端端口自动探测（优先 8001）
$backendPortCandidates = @(8001, 8000, 9001, 9002, 9101)
$BACKEND_PORT = $null
foreach ($port in $backendPortCandidates) {
    if (Test-PortAvailable $port) {
        $BACKEND_PORT = $port
        break
    }
}
if (-not $BACKEND_PORT) {
    Write-Host "✗ 未找到可用后端端口（已尝试: $($backendPortCandidates -join ', ')）" -ForegroundColor Red
    Write-Host "请关闭占用端口的程序，或扩大候选端口列表" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "✓ 后端端口: $BACKEND_PORT" -ForegroundColor Green

# 2. 检查依赖
Write-Host ""
Write-Host "[2/5] 检查 Python 依赖..." -ForegroundColor Yellow
$checkResult = & $PYTHON -c "import fastapi, uvicorn, sqlalchemy, jinja2, playwright; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 依赖已安装" -ForegroundColor Green
} else {
    Write-Host "✗ 依赖缺失" -ForegroundColor Red
    Write-Host "请运行: pip install -r requirements.txt" -ForegroundColor Yellow
    pause
    exit 1
}

# 2.1 检查 Playwright 浏览器（Chromium）
Write-Host ""
Write-Host "[2.1/5] 检查 Playwright Chromium..." -ForegroundColor Yellow
$pwCheck = & $PYTHON -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(args=['--no-sandbox']); b.close(); p.stop(); print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Chromium 可用" -ForegroundColor Green
} else {
    Write-Host "✗ Chromium 未就绪（PDF 导出会 503）" -ForegroundColor Red
    Write-Host "请执行以下命令安装浏览器后重试：" -ForegroundColor Yellow
    Write-Host "  python -m playwright install chromium" -ForegroundColor White
    Write-Host ""
    Write-Host "如果网络较慢，可设置镜像源后再安装：" -ForegroundColor Yellow
    Write-Host "  `$env:PLAYWRIGHT_DOWNLOAD_HOST = 'https://npmmirror.com/mirrors/playwright'" -ForegroundColor White
    Write-Host "  `$env:PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT = '120000'" -ForegroundColor White
    Write-Host "  python -m playwright install chromium" -ForegroundColor White
    pause
    exit 1
}

# 3. 检查数据库
Write-Host ""
Write-Host "[3/5] 检查数据库..." -ForegroundColor Yellow
if (-not (Test-Path "perf_calc.db")) {
    Write-Host "初始化数据库..." -ForegroundColor Yellow
    & $PYTHON -m alembic upgrade head
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 数据库初始化完成" -ForegroundColor Green
    } else {
        Write-Host "✗ 数据库初始化失败" -ForegroundColor Red
        pause
        exit 1
    }
} else {
    Write-Host "✓ 数据库已存在" -ForegroundColor Green
}

# 4. 检查前端依赖
Write-Host ""
Write-Host "[4/5] 检查前端依赖..." -ForegroundColor Yellow
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "安装前端依赖（这可能需要几分钟）..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    $npmResult = $LASTEXITCODE
    Pop-Location
    if ($npmResult -eq 0) {
        Write-Host "✓ 前端依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "✗ 前端依赖安装失败" -ForegroundColor Red
        pause
        exit 1
    }
} else {
    Write-Host "✓ 前端依赖已安装" -ForegroundColor Green
}

# 5. 停止旧进程
Write-Host ""
Write-Host "[5/5] 清理旧进程..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*python*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Write-Host "✓ 清理完成" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动后端
Write-Host "启动后端服务 (端口 $BACKEND_PORT)..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:Root
    & $using:PYTHON -m uvicorn app.main:app --host 127.0.0.1 --port $using:BACKEND_PORT 2>&1
}

# 等待后端启动
Write-Host "等待后端就绪..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 检查后端
$backendOK = $false
$backendBaseUrl = "http://127.0.0.1:$BACKEND_PORT"
for ($i = 1; $i -le 10; $i++) {
    $backendState = Get-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    if (-not $backendState -or $backendState.State -ne "Running") {
        Write-Host "✗ 后端进程提前退出" -ForegroundColor Red
        break
    }

    try {
        $health = Invoke-RestMethod -Uri "$backendBaseUrl/health" -TimeoutSec 2
        if ($health.status -eq "healthy") {
            $backendOK = $true
            Write-Host "✓ 后端启动成功" -ForegroundColor Green
            break
        }
    } catch {}

    Write-Host "  等待... ($i/10)" -ForegroundColor Gray
    Start-Sleep -Seconds 1
}

if (-not $backendOK) {
    Write-Host "✗ 后端启动失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "错误信息:" -ForegroundColor Yellow
    Receive-Job $backendJob | Write-Host
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    pause
    exit 1
}

# 启动前端
Write-Host ""
Write-Host "启动前端服务 (端口 3000)..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:Root\frontend
    # 让 Vite 代理指向当前脚本选定的后端端口。
    $env:VITE_BACKEND_URL = "http://localhost:$using:BACKEND_PORT"
    npm run dev 2>&1
}

# 等待前端启动
Write-Host "等待前端就绪..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 检查前端
$frontendOK = $false
for ($i = 1; $i -le 10; $i++) {
    $frontendState = Get-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    if (-not $frontendState -or $frontendState.State -ne "Running") {
        Write-Host "✗ 前端进程提前退出" -ForegroundColor Red
        break
    }

    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
            $frontendOK = $true
            Write-Host "✓ 前端启动成功" -ForegroundColor Green
            break
        }
    } catch {}

    Write-Host "  等待... ($i/10)" -ForegroundColor Gray
    Start-Sleep -Seconds 1
}

if (-not $frontendOK) {
    Write-Host "✗ 前端启动失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "错误信息:" -ForegroundColor Yellow
    Receive-Job $frontendJob | Write-Host
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    pause
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  🎉 系统启动成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址：" -ForegroundColor Cyan
Write-Host "  前端界面: http://localhost:3000" -ForegroundColor White
Write-Host "  后端 API: http://localhost:$BACKEND_PORT" -ForegroundColor White
Write-Host "  API 文档: http://localhost:$BACKEND_PORT/docs" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 打开浏览器
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

# 保持运行并监控
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  服务运行中..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    while ($true) {
        # 检查后端
        $backendState = Get-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
        if (-not $backendState -or $backendState.State -ne "Running") {
            Write-Host "✗ 后端服务已停止" -ForegroundColor Red
            Receive-Job $backendJob -ErrorAction SilentlyContinue
            break
        }
        
        # 检查前端
        $frontendState = Get-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
        if (-not $frontendState -or $frontendState.State -ne "Running") {
            Write-Host "✗ 前端服务已停止" -ForegroundColor Red
            Receive-Job $frontendJob -ErrorAction SilentlyContinue
            break
        }
        
        Start-Sleep -Seconds 5
    }
} finally {
    Write-Host ""
    Write-Host "正在停止服务..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    
    # 清理进程
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -like "*python*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✓ 服务已停止" -ForegroundColor Green
}
