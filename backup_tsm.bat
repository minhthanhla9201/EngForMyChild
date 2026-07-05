@echo off
setlocal

REM ==================================================
REM Chuyển vào thư mục web
REM ==================================================
cd /d "%~dp0web"

echo.
echo ==========================================
echo BAT DAU BACKUP SQLITE LEN GITHUB RELEASE
echo ==========================================
echo.

REM ==================================================
REM Tạo timestamp
REM Ví dụ:
REM backup-20260616-223015
REM ==================================================
for /f %%i in (
    'powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"'
) do (
    set TAG=backup-%%i
)

echo [INFO] Tag: %TAG%

REM ==================================================
REM Kiểm tra database
REM ==================================================
if not exist db.sqlite3 (
    echo [ERROR] Khong tim thay file db.sqlite3
    exit /b 1
)

REM ==================================================
REM Tạo thư mục backup
REM ==================================================
if not exist backup (
    mkdir backup
)

REM ==================================================
REM Tên file backup
REM ==================================================
set SQLITE_FILE=backup\backup.sqlite3
set ZIP_FILE=backup\%TAG%.zip

REM ==================================================
REM Copy database
REM ==================================================
echo [INFO] Dang sao chep database...

copy /Y db.sqlite3 "%SQLITE_FILE%" >nul

if errorlevel 1 (
    echo [ERROR] Khong the sao chep database
    exit /b 1
)

REM ==================================================
REM Xóa zip cũ nếu tồn tại
REM ==================================================
if exist "%ZIP_FILE%" del /q "%ZIP_FILE%"

REM ==================================================
REM Nén database
REM ==================================================
echo [INFO] Dang nen database...

powershell -NoProfile -Command ^
"Compress-Archive -Path '%SQLITE_FILE%' -DestinationPath '%ZIP_FILE%' -Force -ErrorAction Stop"

if errorlevel 1 (
    echo [ERROR] Khong the tao file ZIP
    del /q "%SQLITE_FILE%" 2>nul
    exit /b 1
)

echo [INFO] Da tao: %ZIP_FILE%

REM ==================================================
REM Kiểm tra GitHub CLI
REM ==================================================
gh auth status >nul 2>&1

if errorlevel 1 (
    echo [ERROR] GitHub CLI chua dang nhap
    echo [INFO] Chay lenh: gh auth login

    del /q "%SQLITE_FILE%" 2>nul
    del /q "%ZIP_FILE%" 2>nul

    exit /b 1
)

REM ==================================================
REM Tạo GitHub Release
REM gh sẽ tự tạo tag nếu chưa tồn tại
REM ==================================================
echo [INFO] Dang upload len GitHub Release...

gh release create %TAG% "%ZIP_FILE%" ^
    --title "%TAG%" ^
    --notes "Automatic SQLite backup"

if errorlevel 1 (
    echo [ERROR] Tao GitHub Release that bai

    del /q "%SQLITE_FILE%" 2>nul
    del /q "%ZIP_FILE%" 2>nul

    exit /b 1
)

REM ==================================================
REM Dọn file tạm
REM ==================================================
del /q "%SQLITE_FILE%" 2>nul
del /q "%ZIP_FILE%" 2>nul

REM ==================================================
REM Don release backup cu (giu 14 ban moi nhat)
REM ==================================================
echo [INFO] Dang don release backup cu (giu 14 ban moi nhat)...

powershell -NoProfile -Command ^
"$keep=14; gh release list --limit 200 --json tagName,createdAt | ConvertFrom-Json | Where-Object { $_.tagName -like 'backup-*' } | Sort-Object createdAt -Descending | Select-Object -Skip $keep | ForEach-Object { Write-Host ('[INFO] Xoa release cu: ' + $_.tagName); gh release delete $_.tagName --yes --cleanup-tag }"

echo.
echo ==========================================
echo BACKUP THANH CONG
echo ==========================================
echo.

exit /b 0