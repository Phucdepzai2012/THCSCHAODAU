@echo off
chcp 65001 >nul
title CỔNG THÔNG TIN THCS NGÔ VĂN SỞ - CHẠY NỘI BỘ
cls
echo ======================================================================
echo    TRƯỜNG THCS NGÔ VĂN SỞ - CHẠY TRANG WEB NỘI BỘ (MÁY TÍNH & WI-FI)
echo ======================================================================
echo.

cd /d "%~dp0"
python app.py

pause
