# interface.py (3단 레이아웃 통합 버전)

import customtkinter
import threading
import datetime
import time
import pyautogui
import pyperclip
from tkinter import messagebox
from btn_commands import (
    open_eduptl, do_login_only, neis_attendace, neis_haengteuk,
    neis_hakjjong, neis_class_hakjjong, browser_manager
)

# --- UI 기본 설정 ---
customtkinter.set_appearance_mode("System")  # PC의 다크/라이트 모드를 따라감
customtkinter.set_default_color_theme("blue")  # 파란색 테마


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- INPUT_MODES 딕셔너리 (Tab 키 횟수 설정) ---
        self.INPUT_MODES = {
            "행동특성 (행발) / 교과세특 (중/고)": 2, 
            "자율활동 (초)": 2, 
            "진로활동 (초)": 2,
            "학기말 종합의견 (초)": 3, 
            "자율활동 (중/고)": 3, 
            "동아리활동 (중/고)": 3,
            "진로활동 (중/고)": 4
        }

        # --- 자동화 상태 변수 ---
        self.stop_automation = False
        self.automation_running = False

        # --- 폰트 설정 (가독성 개선) ---
        self.font_title = customtkinter.CTkFont(family="맑은 고딕", size=24, weight="bold")
        self.font_subtitle = customtkinter.CTkFont(family="맑은 고딕", size=13, weight="normal")
        self.font_button = customtkinter.CTkFont(family="맑은 고딕", size=14, weight="bold")
        self.font_log_title = customtkinter.CTkFont(family="맑은 고딕", size=16, weight="bold")
        self.font_log = customtkinter.CTkFont(family="맑은 고딕", size=12, weight="normal")
        self.font_small_button = customtkinter.CTkFont(family="맑은 고딕", size=12, weight="bold")
        self.font_paste_title = customtkinter.CTkFont(family="맑은 고딕", size=16, weight="bold")

        # --- 윈도우(창) 설정 ---
        self.title("업무포털 자동화 프로그램 v3.0")
        self.geometry("1200x700") # 3단 레이아웃을 위해 너비를 좀 더 넓힙니다.
        
        # 창 닫기 이벤트 처리
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
          # --- [핵심 수정 부분] ---
        # 그리드 레이아웃 설정 - weight를 모두 정수로 변경
        self.grid_columnconfigure(0, weight=2)   # 왼쪽: 자동화 버튼
        self.grid_columnconfigure(1, weight=3)   # 가운데: 스마트 붙여넣기
        self.grid_columnconfigure(2, weight=4)   # 오른쪽: 로그
        self.grid_rowconfigure(0, weight=1)

        # UI 생성
        self.create_left_frame()    # 왼쪽 프레임 (기존 자동화 버튼들)
        self.create_middle_frame()  # 가운데 프레임 (스마트 붙여넣기)
        self.create_right_frame()   # 오른쪽 프레임 (로그)
        
        # --- 초기 로그 메시지 추가 ---
        self.add_log("프로그램이 준비되었습니다.")

    def create_left_frame(self):
        """왼쪽 프레임 (기존 자동화 작업 버튼들)을 생성"""
        self.left_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # UI 제목
        self.label_title = customtkinter.CTkLabel(
            self.left_frame, 
            text="업무포털 자동화", 
            font=self.font_title,
            text_color="#1f538d"
        )
        self.label_title.pack(pady=(15, 10), padx=10)
        
        # 부제목
        self.label_subtitle = customtkinter.CTkLabel(
            self.left_frame,
            text="업무 자동화를 위한 다양한 기능",
            font=self.font_subtitle,
            text_color="#5a5a5a"
        )
        self.label_subtitle.pack(pady=(0, 15), padx=10)

        # 자동화 작업 버튼들
        self.create_automation_buttons()

    def create_middle_frame(self):
        """가운데 프레임 (스마트 붙여넣기 기능)을 생성"""
        self.middle_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.middle_frame.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")

        # 제목
        paste_title = customtkinter.CTkLabel(
            self.middle_frame,
            text="스마트 붙여넣기",
            font=self.font_paste_title,
            text_color="#1f538d"
        )
        paste_title.pack(pady=(15, 10), padx=10)

        # 내용 입력 라벨
        content_label = customtkinter.CTkLabel(
            self.middle_frame,
            text="붙여넣을 내용 (한 줄에 하나씩):",
            font=self.font_subtitle
        )
        content_label.pack(anchor="w", padx=15, pady=(5, 5))

        # 내용 입력 텍스트박스
        self.paste_textbox = customtkinter.CTkTextbox(
            self.middle_frame,
            height=250,
            font=self.font_log,
            corner_radius=8
        )
        self.paste_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # 설정 프레임 (내문 아래)
        settings_frame = customtkinter.CTkFrame(self.middle_frame, corner_radius=8)
        settings_frame.pack(fill="x", padx=15, pady=(0, 10))

        # 항목 선택 라벨
        mode_label = customtkinter.CTkLabel(
            settings_frame,
            text="입력 항목 선택:",
            font=self.font_subtitle
        )
        mode_label.pack(anchor="w", padx=10, pady=(10, 5))

        # 항목 선택 콤보박스
        self.mode_combobox = customtkinter.CTkComboBox(
            settings_frame,
            values=list(self.INPUT_MODES.keys()),
            font=self.font_subtitle,
            state="readonly"
        )
        self.mode_combobox.pack(fill="x", padx=10, pady=(0, 10))
        self.mode_combobox.set(list(self.INPUT_MODES.keys())[0])  # 첫 번째 항목으로 기본 선택

        # 버튼 프레임
        button_frame = customtkinter.CTkFrame(self.middle_frame, corner_radius=8)
        button_frame.pack(fill="x", padx=15, pady=(0, 10))

        # 자동 입력 시작 버튼
        self.start_paste_button = customtkinter.CTkButton(
            button_frame,
            text="자동 입력 시작",
            command=self.start_paste_automation,
            font=self.font_button,
            height=40,
            corner_radius=8
        )
        self.start_paste_button.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)

        # 중단 버튼
        self.stop_paste_button = customtkinter.CTkButton(
            button_frame,
            text="중단",
            command=self.stop_paste_automation,
            font=self.font_button,
            height=40,
            corner_radius=8,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_paste_button.pack(side="right", fill="x", expand=True, padx=(5, 10), pady=10)

        # 상태 라벨
        self.paste_status_label = customtkinter.CTkLabel(
            self.middle_frame,
            text="준비됨",
            font=self.font_subtitle
        )
        self.paste_status_label.pack(pady=(0, 15))

    def create_right_frame(self):
        """오른쪽 프레임 (로그)을 생성"""
        self.right_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.right_frame.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="nsew")

        # 로그 제목
        self.log_title = customtkinter.CTkLabel(
            self.right_frame,
            text="작업 로그",
            font=self.font_log_title,
            text_color="#1f538d"
        )
        self.log_title.pack(pady=(15, 10), padx=10)

        # 로그 출력 텍스트 박스
        self.log_textbox = customtkinter.CTkTextbox(
            self.right_frame, 
            state="disabled", 
            corner_radius=8, 
            font=self.font_log,
            wrap="word"
        )
        self.log_textbox.pack(expand=True, fill="both", padx=15, pady=(0, 10))
        
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
        self.clear_log_button.pack(pady=(0, 15))

    def create_automation_buttons(self):
        """자동화 작업 버튼들을 생성하는 함수"""
        button_configs = [
            {"text": "업무포털 접속", "command": self.run_open_eduptl},
            {"text": "업무포털 로그인", "command": self.run_do_login_only},
            {"text": "나이스 출결 바로가기", "command": self.run_neis_attendace},
            {"text": "행동특성 및 종합의견 입력", "command": self.run_neis_haengteuk},
            {"text": "학기말 종합의견 (담임)", "command": self.run_neis_hakjjong},
            {"text": "학기말 종합의견 (교과)", "command": self.run_neis_class_hakjjong}
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

    # --- 스마트 붙여넣기 관련 메소드들 ---
    def start_paste_automation(self):
        """자동 붙여넣기를 시작합니다."""
        content = self.paste_textbox.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("경고", "붙여넣을 내용을 입력해주세요.")
            return
        
        selected_mode = self.mode_combobox.get()
        if selected_mode not in self.INPUT_MODES:
            messagebox.showerror("오류", "유효한 항목을 선택해주세요.")
            return

        # 버튼 상태 변경
        self.start_paste_button.configure(state="disabled")
        self.stop_paste_button.configure(state="normal")
        self.automation_running = True
        self.stop_automation = False
        
        # 로그 출력
        self.add_log(f"스마트 붙여넣기 시작 - {selected_mode}")
        
        # 데이터 준비
        data_list = [line.strip() for line in content.split('\n') if line.strip()]
        tab_count = self.INPUT_MODES[selected_mode]
        
        # 별도 스레드에서 자동화 실행
        thread = threading.Thread(
            target=self.run_paste_thread, 
            args=(data_list, tab_count), 
            daemon=True
        )
        thread.start()

    def stop_paste_automation(self):
        """자동화를 중지합니다."""
        self.stop_automation = True
        self.update_paste_status("중지 중...")
        self.add_log("스마트 붙여넣기 중지 요청")

    def run_paste_thread(self, data_list, tab_count):
        """실제 자동화 로직을 실행합니다."""
        try:
            total_items = len(data_list)
            self.add_log(f"총 {total_items}개 항목을 처리합니다. Tab 횟수: {tab_count}")
            
            # 3초 카운트다운
            for i in range(3, 0, -1):
                if self.stop_automation:
                    return
                self.update_paste_status(f"{i}초 후 시작...")
                time.sleep(1)
            
            if self.stop_automation:
                return
            
            self.update_paste_status("자동 붙여넣기 진행 중...")
            
            # 각 항목을 순서대로 처리
            for idx, data in enumerate(data_list, 1):
                if self.stop_automation:
                    break
                
                self.update_paste_status(f"진행 중... ({idx}/{total_items})")
                
                # 클립보드에 텍스트 복사
                pyperclip.copy(data)
                
                # 짧은 대기
                time.sleep(0.1)
                
                # Ctrl+V로 붙여넣기
                pyautogui.hotkey('ctrl', 'v')
                
                # 지정된 횟수만큼 Tab 키 누르기
                time.sleep(0.2)
                for _ in range(tab_count):
                    pyautogui.press('tab')
                    time.sleep(0.1)
                
                # 다음 입력을 위한 대기
                time.sleep(0.5)
                
                # 로그 출력
                self.add_log(f"[{idx}/{total_items}] 처리 완료: {data[:30]}{'...' if len(data) > 30 else ''}")
            
            if not self.stop_automation:
                self.update_paste_status("완료!")
                self.add_log("스마트 붙여넣기가 모두 완료되었습니다.")
                self.after(3000, lambda: self.update_paste_status("준비됨"))
            else:
                self.update_paste_status("중지됨")
                self.add_log("스마트 붙여넣기가 중지되었습니다.")
                
        except Exception as e:
            error_msg = f"스마트 붙여넣기 중 오류 발생: {str(e)}"
            self.update_paste_status("오류 발생")
            self.add_log(error_msg)
            self.after(0, lambda: messagebox.showerror("오류", error_msg))
        finally:
            # 버튼 상태 복원
            self.after(0, self.reset_paste_buttons)

    def update_paste_status(self, message):
        """붙여넣기 상태 라벨을 업데이트합니다."""
        self.after(0, lambda: self.paste_status_label.configure(text=message))

    def reset_paste_buttons(self):
        """붙여넣기 버튼 상태를 초기 상태로 돌립니다."""
        self.start_paste_button.configure(state="normal")
        self.stop_paste_button.configure(state="disabled")
        self.automation_running = False

    # --- 기존 기능들 (로그, 자동화 작업) ---
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

    def on_closing(self):
        """창이 닫힐 때 호출될 함수 - 브라우저 리소스를 안전하게 정리"""
        if self.automation_running:
            self.stop_automation = True
            time.sleep(0.2)  # 자동화 중지 대기
        
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