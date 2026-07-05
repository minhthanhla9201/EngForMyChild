@echo off
REM Di chuyển vào thư mục web
cd /d "%~dp0web"

REM Chạy waitress từ môi trường ảo
..\.venv\Scripts\python.exe -m waitress --listen=0.0.0.0:9001 config.wsgi:application