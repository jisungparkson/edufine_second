# paste_helper.py - NEIS 스마트 붙여넣기 도우미

import customtkinter
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time
import pyautogui
import pyperclip

class PasteHelperWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # 창 설정
        self.title("NEIS 스마트 붙여넣기 도우미")
        self.geometry("600x500")
        self.resizable(True, True)
        
        # 부모 창 위에 표시되도록 설정
        self.transient(parent)
        self.grab_set()
        
        # 폰트 설정
        self.font_title = customtkinter.CTkFont(family="맑은 고딕", size=16, weight="bold")
        self.font_normal = customtkinter.CTkFont(family="맑은 고딕", size=12, weight="normal")
        self.font_button = customtkinter.CTkFont(family="맑은 고딕", size=12, weight="bold")
        
        # 변수 초기화
        self.stop_automation = False
        self.automation_running = False
        
        # UI 생성
        self.create_widgets()
        
        # 창이 닫힐 때 자동화 중지
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """UI 위젯들을 생성합니다."""
        # 메인 프레임
        main_frame = customtkinter.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 제목
        title_label = customtkinter.CTkLabel(
            main_frame,
            text="NEIS 스마트 붙여넣기 도우미",
            font=self.font_title
        )
        title_label.pack(pady=(10, 20))
        
        # 설명 텍스트
        desc_text = """사용 방법:
1. 아래 텍스트 상자에 붙여넣을 내용을 입력하세요 (한 줄에 하나씩)
2. '자동 붙여넣기 시작' 버튼을 클릭하세요
3. 3초 후 자동으로 각 줄을 순서대로 붙여넣기 시작합니다
4. Tab 키로 다음 입력 필드로 이동합니다
5. 중지하려면 '중지' 버튼을 클릭하세요"""
        
        desc_label = customtkinter.CTkLabel(
            main_frame,
            text=desc_text,
            font=self.font_normal,
            justify="left"
        )
        desc_label.pack(pady=(0, 15), padx=20)
        
        # 텍스트 입력 영역
        text_frame = customtkinter.CTkFrame(main_frame)
        text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        text_label = customtkinter.CTkLabel(
            text_frame,
            text="붙여넣을 내용 (한 줄에 하나씩):",
            font=self.font_normal
        )
        text_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # 텍스트박스 (tkinter의 ScrolledText 사용)
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            height=10,
            font=("맑은 고딕", 11),
            wrap=tk.WORD
        )
        self.text_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 버튼 프레임
        button_frame = customtkinter.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # 자동 붙여넣기 시작 버튼
        self.start_button = customtkinter.CTkButton(
            button_frame,
            text="자동 붙여넣기 시작",
            font=self.font_button,
            command=self.start_automation,
            height=35
        )
        self.start_button.pack(side="left", padx=(10, 5), pady=10, expand=True, fill="x")
        
        # 중지 버튼
        self.stop_button = customtkinter.CTkButton(
            button_frame,
            text="중지",
            font=self.font_button,
            command=self.stop_automation_func,
            height=35,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_button.pack(side="right", padx=(5, 10), pady=10, expand=True, fill="x")
        
        # 상태 라벨
        self.status_label = customtkinter.CTkLabel(
            main_frame,
            text="준비됨",
            font=self.font_normal
        )
        self.status_label.pack(pady=(0, 10))

    def start_automation(self):
        """자동 붙여넣기를 시작합니다."""
        content = self.text_area.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("경고", "붙여넣을 내용을 입력해주세요.")
            return
        
        # 버튼 상태 변경
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.automation_running = True
        self.stop_automation = False
        
        # 별도 스레드에서 자동화 실행
        thread = threading.Thread(target=self.run_automation, args=(content,), daemon=True)
        thread.start()

    def stop_automation_func(self):
        """자동화를 중지합니다."""
        self.stop_automation = True
        self.update_status("중지 중...")

    def run_automation(self, content):
        """실제 자동화 로직을 실행합니다."""
        try:
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            total_lines = len(lines)
            
            # 3초 카운트다운
            for i in range(3, 0, -1):
                if self.stop_automation:
                    return
                self.update_status(f"{i}초 후 시작...")
                time.sleep(1)
            
            if self.stop_automation:
                return
            
            self.update_status("자동 붙여넣기 시작!")
            
            # 각 줄을 순서대로 처리
            for idx, line in enumerate(lines, 1):
                if self.stop_automation:
                    break
                
                self.update_status(f"진행 중... ({idx}/{total_lines})")
                
                # 클립보드에 텍스트 복사
                pyperclip.copy(line)
                
                # 짧은 대기
                time.sleep(0.1)
                
                # Ctrl+V로 붙여넣기
                pyautogui.hotkey('ctrl', 'v')
                
                # Tab 키로 다음 필드로 이동
                time.sleep(0.2)
                pyautogui.press('tab')
                
                # 다음 입력을 위한 대기
                time.sleep(0.5)
            
            if not self.stop_automation:
                self.update_status("완료!")
                self.after(2000, lambda: self.update_status("준비됨"))
            else:
                self.update_status("중지됨")
                
        except Exception as e:
            error_msg = f"오류 발생: {str(e)}"
            self.update_status(error_msg)
            self.after(0, lambda: messagebox.showerror("오류", error_msg))
        finally:
            # 버튼 상태 복원
            self.after(0, self.reset_buttons)

    def update_status(self, message):
        """상태 라벨을 업데이트합니다."""
        self.after(0, lambda: self.status_label.configure(text=message))

    def reset_buttons(self):
        """버튼 상태를 초기 상태로 돌립니다."""
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.automation_running = False

    def on_closing(self):
        """창이 닫힐 때 호출되는 함수"""
        if self.automation_running:
            self.stop_automation = True
            time.sleep(0.1)  # 자동화 중지 대기
        
        self.grab_release()
        self.destroy()