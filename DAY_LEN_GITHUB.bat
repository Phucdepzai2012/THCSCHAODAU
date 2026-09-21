@echo off
chcp 65001 >nul
title ĐẨY TOÀN BỘ WEBSITE LÊN GITHUB
cls
echo ======================================================================
echo    CỔNG THÔNG TIN THCS NGÔ VĂN SỞ - TỰ ĐỘNG ĐẨY MÃ NGUỒN LÊN GITHUB
echo ======================================================================
echo.
echo Bước 1: Hãy vào trang https://github.com/new và tạo 1 Repository mới (để chế độ Public).
echo Bước 2: Sao chép đường link Repository vừa tạo (Ví dụ: https://github.com/ten-ban/thcs-ngovanso.git)
echo.
set /p REPO_URL=">>> Dán đường link GitHub của bạn vào đây rồi bấm Enter: "

if "%REPO_URL%"=="" (
    echo [!] Ban chua nhap link GitHub!
    pause
    exit /b
)

echo.
echo Đang đóng gói và đẩy mã nguồn lên GitHub...
cd /d "%~dp0"
git init
git branch -M main
git remote remove origin 2>nul
git remote add origin %REPO_URL%
git add .
git commit -m "Upload THCS Ngo Van So Portal" 2>nul
git push -u origin main --force

echo.
echo ======================================================================
echo 🎉 HOÀN TẤT ĐẨY LÊN GITHUB!
echo Bây giờ bạn chỉ cần vào https://render.com để bật chạy 24/7!
echo ======================================================================
echo.
pause
