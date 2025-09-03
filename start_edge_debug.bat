
@echo off
setlocal

REM config.ini에서 user_data_dir 읽기
for /f "tokens=2 delims== " %%i in ('findstr "user_data_dir" config.ini') do set USER_DATA_DIR=%%i

REM 기본값 설정 (config.ini에서 찾지 못한 경우)
if "%USER_DATA_DIR%"=="" set USER_DATA_DIR=C:\temp\edge-debug

echo Edge 디버그 모드로 시작 중...
echo 사용자 데이터 디렉토리: %USER_DATA_DIR%
start msedge --remote-debugging-port=9222 --user-data-dir="%USER_DATA_DIR%"
echo Edge가 디버그 모드로 시작되었습니다.
echo 이제 프로그램에서 기존 브라우저에 연결할 수 있습니다.
pause
