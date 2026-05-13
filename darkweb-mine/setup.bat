@echo off
chcp 65001 >nul
title 暗网帝国矿机 - 一键部署

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║     暗 网 帝 国 数 字 考 古 矿 机 - 部 署 程 序     ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装 Python 3.8+
    echo 下载地址: https://python.org 或使用 Microsoft Store
    pause
    exit /b 1
)
echo [✓] Python 已检测到

:: 安装依赖
echo.
echo [*] 安装依赖 (使用清华镜像)...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
if %errorlevel% neq 0 (
    echo [!] 依赖安装失败，尝试默认源...
    pip install -r requirements.txt -q
)
echo [✓] 依赖安装完成

:: 初始化
echo.
echo [*] 运行环境初始化...
python main.py --setup
if %errorlevel% neq 0 (
    echo [!] 初始化遇到问题，请检查
    pause
    exit /b 1
)

:: 创建Windows定时任务（每2小时运行一次）
echo.
echo [*] 设置全自动定时任务...
set SCRIPT_DIR=%~dp0
set TASK_NAME=EmpireMinerAutoScan

:: 先删除旧任务（如果存在）
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: 创建新任务 - 每2小时运行一次
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "python %SCRIPT_DIR%main.py --once" ^
    /sc hourly /mo 2 ^
    /st 00:00 ^
    /f ^
    /rl limited

if %errorlevel% equ 0 (
    echo [✓] 定时任务已创建: %TASK_NAME%
    echo      - 每2小时自动运行一次
    echo      - 可在"任务计划程序"中管理
) else (
    echo [!] 定时任务创建失败，请以管理员身份运行此脚本
)

:: 测试运行
echo.
echo [*] 执行测试运行...
python main.py --once

echo.
echo ══════════════════════════════════════════════════════
echo   部署完成！帝国矿机已开始全自动运行。
echo.
echo   命令速查:
echo     python main.py --once     单次扫描
echo     python main.py --report   查看发现
echo     python main.py --stats    查看统计
echo     python main.py --loop     持续循环运行
echo.
echo   数据文件:
echo     data\empire.db            考古数据库
echo     data\miner.log            运行日志
echo     data\discoveries.json     发现记录
echo ══════════════════════════════════════════════════════
echo.
pause
