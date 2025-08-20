# interface.py (스레드 기반 버전)
import tkinter as tk
import threading
from btn_commands import (
    open_eduptl, do_login_only, neis_attendace, neis_haengteuk,
    neis_hakjjong, neis_class_hakjjong
)

def run_in_thread(func):
    """함수를 별도 스레드에서 실행하여 GUI 응답성을 유지합니다"""
    thread = threading.Thread(target=func, daemon=True)
    thread.start()

# ➊ 기본 스타일 정의
bgcolor = '#005887'
font_color = '#F5F5F5'
font = lambda size, bold: ('맑은 고딕', size, 'bold') if bold else ('맑은 고딕', size)

# ➋ 화면 설정
window = tk.Tk()
window.title("업무포털 자동화 (Playwright) v2")
window.geometry('500x600')
window.configure(bg=bgcolor)

# ➌ 제목, 설명, 바닥글
title = tk.Label(window, text="업무포털 자동화", font=font(25, True), bg=bgcolor, fg=font_color, wraplength=500)
title.place(relx=0.5, rely=0.08, anchor=tk.CENTER)

subtitle = tk.Label(window, text="업무 자동화를 위한 다양한 기능을 선택하세요", font=font(12, False), bg=bgcolor, fg=font_color)
subtitle.place(relx=0.5, rely=0.17, anchor=tk.CENTER)

footer = tk.Label(window, text="© 2024 Szzng. All rights reserved.", font=font(10, False), bg=bgcolor, fg=font_color)
footer.place(relx=0.5, rely=0.95, anchor=tk.CENTER)

# ➏ 버튼
btn_styles = {
    'font': font(12, True),
    'width': 35,
    'height': 2,
    'bd': 3,
    'bg': 'white',
    'fg': bgcolor,
    'cursor': 'hand2',
    'relief': 'raised'
}

# 스레드에서 함수 실행으로 GUI 응답성 확보
btn_options = [
    {"text": "업무포털 접속", "command": lambda: run_in_thread(open_eduptl)},
    {"text": "업무포털 로그인", "command": lambda: run_in_thread(do_login_only)},
    {"text": "나이스 출결 바로가기", "command": lambda: run_in_thread(neis_attendace)},
    {"text": "행동특성 및 종합의견 붙여넣기", "command": lambda: run_in_thread(neis_haengteuk)},
    {"text": "학기말 종합의견 (담임)", "command": lambda: run_in_thread(neis_hakjjong)},
    {"text": "학기말 종합의견 (교과)", "command": lambda: run_in_thread(neis_class_hakjjong)}
]

# 버튼 배치
for idx, option in enumerate(btn_options):
    button = tk.Button(window, text=option["text"], command=option["command"], **btn_styles)
    button.place(relx=0.5, rely=0.28 + 0.11 * idx, anchor=tk.CENTER)

# ❼ 만든 화면 실행
window.mainloop()