@echo off
chcp 65001 >nul
title CỔNG THÔNG TIN THCS NGÔ VĂN SỞ - MỞ LINK CỘNG ĐỒNG
cls
echo ======================================================================
echo    TRƯỜNG THCS NGÔ VĂN SỞ - HỆ THỐNG CỔNG THÔNG TIN ĐIỆN TỬ
echo ======================================================================
echo.
echo Đang khởi chạy máy chủ website và tạo đường Link Online cho cộng đồng...
echo Vui lòng đợi trong giây lát...
echo.

cd /d "%~dp0"
python share_public.py

pause
