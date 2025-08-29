# interface.py (CustomTkinter를 사용한 새 버전)

import customtkinter
import threading
import datetime
from tkinter import messagebox
from btn_commands import (
    open_eduptl, do_login_only, neis_attendace, neis_haengteuk,
    neis_hakjjong, neis_class_hakjjong, browser_manager, open_paste_helper
)

# --- UI 기본 설정 ---
customtkinter.set_appearance_mode("System")  # PC의 다크/라이트 모드를 따라감
customtkinter.set_default_color_theme("blue")  # 파란색 테마


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- 폰트 설정 (가독성 개선) ---
        self.font_title = customtkinter.CTkFont(family="맑은 고딕", size=26, weight="bold")
        self.font_subtitle = customtkinter.CTkFont(family="맑은 고딕", size=13, weight="normal")
        self.font_button = customtkinter.CTkFont(family="맑은 고딕", size=14, weight="bold")
        self.font_log_title = customtkinter.CTkFont(family="맑은 고딕", size=18, weight="bold")
        self.font_log = customtkinter.CTkFont(family="맑은 고딕", size=13, weight="normal")
        self.font_small_button = customtkinter.CTkFont(family="맑은 고딕", size=12, weight="bold")

        # --- 윈도우(창) 설정 ---
        self.title("업무포털 자동화 프로그램 v3.0")
        self.geometry("900x600")
        
        # 창 닫기 이벤트 처리
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # --- 그리드 레이아웃 설정 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- 왼쪽 프레임 (입력 및 버튼) ---
        self.left_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # UI 제목
        self.label_title = customtkinter.CTkLabel(
            self.left_frame, 
            text="업무포털 자동화", 
            font=self.font_title,
            text_color="#1f538d"
        )
        self.label_title.pack(pady=20, padx=10)
        
        # 부제목
        self.label_subtitle = customtkinter.CTkLabel(
            self.left_frame,
            text="업무 자동화를 위한 다양한 기능을 선택하세요",
            font=self.font_subtitle,
            text_color="#5a5a5a"
        )
        self.label_subtitle.pack(pady=(0, 20), padx=10)

        # 자동화 작업 버튼들
        self.create_automation_buttons()
        
        # --- 오른쪽 프레임 (로그) ---
        self.right_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # 로그 제목
        self.log_title = customtkinter.CTkLabel(
            self.right_frame,
            text="작업 로그",
            font=self.font_log_title,
            text_color="#1f538d"
        )
        self.log_title.pack(pady=(10, 5), padx=10)

        # 로그 출력 텍스트 박스
        self.log_textbox = customtkinter.CTkTextbox(
            self.right_frame, 
            state="disabled", 
            corner_radius=10, 
            font=self.font_log,
            wrap="word"
        )
        self.log_textbox.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        
        # 로그 클리어 버튼
        self.clear_log_button = customtkinter.CTkButton(
            self.right_frame,
            text="로그 지우기",
            command=self.clear_log,
            font=self.font_small_button,
            width=120,
            height=35,
            corner_radius=8
        )
        self.clear_log_button.pack(pady=(0, 10))
        
        # --- 초기 로그 메시지 추가 ---
        self.add_log("프로그램이 준비되었습니다.")

    def create_automation_buttons(self):
        """자동화 작업 버튼들을 생성하는 함수"""
        button_configs = [
            {"text": "업무포털 접속", "command": self.run_open_eduptl},
            {"text": "업무포털 로그인", "command": self.run_do_login_only},
            {"text": "나이스 출결 바로가기", "command": self.run_neis_attendace},
            {"text": "행동특성 및 종합의견 입력", "command": self.run_neis_haengteuk},
            {"text": "학기말 종합의견 (담임)", "command": self.run_neis_hakjjong},
            {"text": "학기말 종합의견 (교과)", "command": self.run_neis_class_hakjjong},
            {"text": "붙여넣기 도우미", "command": self.run_open_paste_helper}
        ]
        
        for config in button_configs:
            button = customtkinter.CTkButton(
                self.left_frame,
                text=config["text"],
                command=config["command"],
                font=self.font_button,
                height=45,
                corner_radius=10
            )
            button.pack(pady=6, padx=20, fill="x")

    def add_log(self, message):
        """로그 텍스트 박스에 메시지를 추가하는 함수"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", log_message + "\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")

    def clear_log(self):
        """로그를 지우는 함수"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.add_log("로그가 지워졌습니다.")

    def run_in_thread_with_log(self, func, func_name):
        """함수를 스레드에서 실행하고 로그를 남기는 헬퍼 함수"""
        def wrapper():
            try:
                self.add_log(f"{func_name} 작업을 시작합니다...")
                func()
                self.add_log(f"{func_name} 작업이 완료되었습니다.")
            except Exception as e:
                error_msg = f"{func_name} 작업 중 오류가 발생했습니다: {str(e)}"
                self.add_log(error_msg)
                # GUI 스레드에서 messagebox 실행
                self.after(0, lambda: messagebox.showerror("오류", error_msg))
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

    # --- 각 자동화 작업을 실행하는 함수들 ---
    def run_open_eduptl(self):
        self.run_in_thread_with_log(open_eduptl, "업무포털 접속")

    def run_do_login_only(self):
        self.run_in_thread_with_log(do_login_only, "업무포털 로그인")

    def run_neis_attendace(self):
        self.run_in_thread_with_log(neis_attendace, "나이스 출결 바로가기")

    def run_neis_haengteuk(self):
        self.run_in_thread_with_log(neis_haengteuk, "행동특성 및 종합의견 입력")

    def run_neis_hakjjong(self):
        self.run_in_thread_with_log(neis_hakjjong, "학기말 종합의견 (담임)")

    def run_neis_class_hakjjong(self):
        self.run_in_thread_with_log(neis_class_hakjjong, "학기말 종합의견 (교과)")

    def run_open_paste_helper(self):
        self.add_log("복사/붙여넣기 도우미를 엽니다.")
        # 이 함수는 GUI 창을 직접 생성하므로 스레드에서 실행하지 않습니다.
        open_paste_helper(self)  # 'self'가 메인 윈도우 인스턴스입니다.

    def on_closing(self):
        """창이 닫힐 때 호출될 함수 - 브라우저 리소스를 안전하게 정리"""
        self.add_log("프로그램을 종료합니다. 브라우저 리소스를 정리합니다...")
        try:
            browser_manager.close()  # Playwright를 안전하게 종료
            self.add_log("브라우저 리소스가 정리되었습니다.")
        except Exception as e:
            self.add_log(f"브라우저 정리 중 오류: {str(e)}")
        finally:
            self.destroy()  # CustomTkinter 창 닫기


if __name__ == "__main__":
    app = App()
    app.mainloop()