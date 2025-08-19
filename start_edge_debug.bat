@echo off
echo Edge 디버그 모드로 시작 중...
start msedge --remote-debugging-port=9222 --user-data-dir="C:\temp\edge-debug"
echo Edge가 디버그 모드로 시작되었습니다.
echo 이제 프로그램에서 기존 브라우저에 연결할 수 있습니다.
pause