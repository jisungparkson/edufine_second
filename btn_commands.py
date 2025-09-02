# btn_commands.py (Sync API 통일 버전)

from playwright.sync_api import sync_playwright, Page, Playwright, Browser, TimeoutError, expect
from utils import (
    urls, login, neis_go_menu, neis_click_btn, get_excel_data, 
    neis_fill_row, switch_tab, open_url_in_new_tab
)
from tkinter import messagebox

class BrowserManager:
    """Playwright의 브라우저 상태를 총괄 관리하는 클래스"""
    def __init__(self):
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.page: Page = None
        print("BrowserManager가 준비되었습니다.")

    def get_page(self) -> Page:
        """
        [배포용 수정 버전]
        항상 새로운 브라우저를 시작하고, 유효한 페이지 객체를 반환합니다.
        """
        # 1. 플레이라이트 인스턴스가 없으면 새로 시작합니다.
        if self.playwright is None:
            print("Playwright 인스턴스를 시작합니다.")
            self.playwright = sync_playwright().start()

        # 2. 브라우저가 없거나, 연결이 끊겼다면 새로 시작합니다.
        #    connect_over_cdp (기존 브라우저 연결) 로직을 완전히 제거합니다.
        if self.browser is None or not self.browser.is_connected():
            print("새 브라우저를 시작합니다.")
            # headless=False는 브라우저 창이 보이도록 하는 옵션입니다.
            self.browser = self.playwright.chromium.launch(headless=False, channel="msedge")

        # 3. 페이지가 없거나 닫혔다면, 새로 만듭니다.
        if self.page is None or self.page.is_closed():
            print("페이지를 새로 생성합니다.")
            # 이미 컨텍스트가 있을 수 있으므로 확인 후 새 페이지를 만듭니다.
            if len(self.browser.contexts) > 0:
                self.page = self.browser.contexts[0].new_page()
            else:
                context = self.browser.new_context()
                self.page = context.new_page()
            
            self.page.set_viewport_size({"width": 1920, "height": 1080})

        return self.page

    def close(self):
        """모든 리소스를 안전하게 종료합니다."""
        try:
            if self.browser and self.browser.is_connected():
                print("브라우저를 닫습니다.")
                self.browser.close()
            if self.playwright:
                print("Playwright 인스턴스를 중지합니다.")
                self.playwright.stop()
        except Exception as e:
            print(f"종료 중 오류 발생: {e}")
        finally:
            # 모든 상태를 초기화합니다.
            self.playwright = None
            self.browser = None
            self.page = None

# 단 하나의 현장 감독 인스턴스 생성
browser_manager = BrowserManager()

def _handle_error(e, app_instance):
    """오류 처리 시, App 인스턴스를 통해 안전하게 UI에 보고합니다."""
    error_message = f"{type(e).__name__}: {e}"
    
    # 이제 messagebox를 직접 호출하지 않습니다.
    # 대신, App의 로그 기능과 메시지 박스 기능을 안전하게 호출합니다.
    if app_instance:
        app_instance.add_log(f"오류 발생: {error_message}")
        app_instance.after(0, lambda: messagebox.showerror("오류 발생", error_message))
    
    browser_manager.close()

def _ensure_valid_session_and_navigate(app_instance, target_service) -> Page:
    """
    세션 확보 및 이동 Gatekeeper 함수
    연계 시스템 자동화를 위한 중앙 관리 함수
    """
    try:
        app_instance.add_log(f"{target_service} 시스템 접근을 위한 세션 상태를 확인합니다...")
        
        # a. 현재 페이지 확인
        current_page = browser_manager.get_page()
        current_url = current_page.url
        app_instance.add_log(f"현재 페이지: {current_url}")
        
        # b. 세션이 불완전할 경우 (수동 로그인 상태)
        if "bpm_man_mn00_001.do" in current_url:
            app_instance.add_log("수동 로그인 상태가 감지되었습니다.")
            app_instance.add_log("연계 시스템 접근을 위해서는 자동 로그인을 통한 완전한 세션 확보가 필요합니다.")
            
            # 더 상세한 설명과 함께 사용자에게 안내
            message = f"""🔐 세션 재확보가 필요합니다

현재 수동 로그인 상태에서는 {target_service} 연계 시스템에 접근할 수 없습니다.

📋 이유:
• 수동 로그인 시 일부 세션 정보가 누락됩니다
• 연계 시스템은 완전한 인증 세션이 필요합니다

✅ 해결방법:
자동 로그인을 통해 완전한 세션을 확보합니다
(config.ini의 비밀번호 파일을 사용)

계속 진행하시겠습니까?"""
            
            answer = messagebox.askyesno("세션 재확보 필요", message)
            if not answer:
                app_instance.add_log("사용자가 자동 로그인을 취소했습니다.")
                messagebox.showinfo("안내", f"{target_service} 시스템 접근이 취소되었습니다.\n\n수동으로 {target_service}에 접근하려면 브라우저에서 직접 이동해주세요.")
                return None
            
            # 전체 자동 로그인 수행
            app_instance.add_log("연계 시스템 접근을 위한 자동 로그인을 시작합니다...")
            login_success = do_login_only(app_instance)
            if not login_success:
                app_instance.add_log("자동 로그인에 실패했습니다.")
                messagebox.showerror("로그인 실패", "자동 로그인에 실패했습니다.\n\nconfig.ini 파일과 비밀번호 파일을 확인해주세요.")
                return None
            
            app_instance.add_log("자동 로그인이 완료되었습니다. 연계 시스템에 접근합니다.")
        
        # c. 세션이 없을 경우
        elif "lg00_001.do" in current_url or current_url == "about:blank":
            app_instance.add_log("세션이 없는 상태입니다. 자동 로그인을 시작합니다.")
            login_success = do_login_only(app_instance)
            if not login_success:
                app_instance.add_log("자동 로그인에 실패했습니다.")
                return None
        
        # d. 세션 확보 후 타겟 서비스로 이동
        app_instance.add_log(f"유효한 세션이 확보되었습니다. {target_service}로 이동합니다.")
        portal_page = browser_manager.get_page()
        
        # 연계 시스템 링크 존재 확인
        try:
            if target_service == "나이스":
                service_link = portal_page.get_by_role("link", name="나이스", exact=True).first
            else:
                raise ValueError(f"지원하지 않는 서비스: {target_service}")
            
            # 링크가 실제로 보이고 클릭 가능한지 확인
            service_link.wait_for(state="visible", timeout=10000)
            app_instance.add_log(f"{target_service} 링크를 확인했습니다. 클릭합니다.")
            
        except Exception as link_error:
            app_instance.add_log(f"{target_service} 링크를 찾을 수 없습니다: {link_error}")
            messagebox.showerror(
                "링크 오류", 
                f"{target_service} 링크를 찾을 수 없습니다.\n\n가능한 원인:\n• 세션이 만료되었습니다\n• 페이지 로딩이 완료되지 않았습니다\n\n해결방법:\n다시 시도하거나 브라우저에서 직접 접근해주세요."
            )
            return None
        
        # 링크 클릭하여 새 창으로 이동
        with portal_page.expect_popup() as popup_info:
            service_link.click()
        
        target_page = popup_info.value
        app_instance.add_log(f"{target_service} 새 창이 열렸습니다. 페이지 로딩을 기다립니다...")
        target_page.wait_for_load_state("networkidle")
        browser_manager.page = target_page
        app_instance.add_log(f"✅ {target_service} 페이지 이동이 성공적으로 완료되었습니다!")
        
        # 성공 메시지 표시
        messagebox.showinfo("접속 성공", f"{target_service} 시스템에 성공적으로 접속했습니다!")
        return target_page
        
    except Exception as e:
        _handle_error(e, app_instance)
        return None

def _navigate_to_neis(app_instance) -> Page:
    return _ensure_valid_session_and_navigate(app_instance, "나이스")


def _wait_for_login_success(page: Page):
    """로그인이 성공했는지 확인하는 공통 함수"""
    print("로그인 성공 확인 중... (페이지 로딩 대기)")
    
    # 페이지 로딩 완료 대기
    page.wait_for_load_state('networkidle', timeout=30000)
    
    current_url = page.url
    print(f"현재 URL: {current_url}")
    
    # 로그인 페이지에서 벗어났는지 확인
    if 'lg00_001.do' not in current_url:
        print("로그인 성공 (URL 확인)")
        return
    
    # 간단한 대기 후 재확인
    page.wait_for_timeout(3000)
    current_url = page.url
    if 'lg00_001.do' not in current_url:
        print("로그인 성공 (재확인)")
        return
    
    print("로그인이 완료되지 않았습니다. 수동으로 로그인을 완료해주세요.")
    messagebox.showinfo("알림", "자동 로그인이 완료되지 않았습니다.\n브라우저에서 수동으로 로그인을 완료한 후 확인을 눌러주세요.")
    
    # 사용자가 수동 로그인 완료할 때까지 대기
    while 'lg00_001.do' in page.url:
        page.wait_for_timeout(1000)
    
    print("로그인 완료 확인됨")

def open_eduptl(app_instance):
    """
    업무포털 '로그인' 페이지로 직접 이동합니다.
    자동으로 로그인을 수행하지는 않습니다.
    """
    try:
        page = browser_manager.get_page()
        page.bring_to_front() # 창을 맨 앞으로 가져옵니다.
        
        print("업무포털 로그인 페이지로 직접 이동합니다...")
        
        # '업무포털 로그인' URL로 직접 이동하도록 수정
        page.goto(urls['업무포털 로그인'])
        
        # 페이지 로딩이 완료될 때까지 기다립니다.
        page.wait_for_load_state('networkidle')
        print("로그인 페이지 로딩 완료.")
        
    except Exception as e:
        _handle_error(e, app_instance) # 오류 발생 시 처리

def do_login_only(app_instance):
    """
    현재 어느 페이지에 있든, 업무포털 로그인 화면으로 이동하여 로그인을 수행합니다.
    """
    try:
        page = browser_manager.get_page()
        page.bring_to_front()

        current_url = page.url
        print(f"현재 페이지 URL: {current_url}")
        
        # --- [핵심 수정 로직] ---
        # 현재 URL에 'eduptl.kr' (업무포털) 주소가 포함되어 있고, 그 페이지가 로그인 페이지가 아닌 경우를 제외하고는
        # 모두 로그인 페이지로 이동시킵니다.
        # 이렇게 하면 about:blank, neis.go.kr 등 어떤 페이지에 있더라도 로그인 페이지로 갑니다.
        if not ('eduptl.kr' in current_url and current_url.endswith('lg00_001.do')):
            
            # 만약 이미 업무포털의 다른 페이지에 있다면, 그냥 로그인 페이지만 띄웁니다.
            if 'eduptl.kr' in current_url:
                print("업무포털의 다른 페이지에 있습니다. 로그인 페이지로 이동합니다...")
                page.goto(urls['업무포털 로그인'])
            # 그 외의 경우 (about:blank, naver.com 등) 에는 업무포털 메인으로 먼저 갑니다.
            else:
                print("업무포털 페이지가 아니므로, 메인 페이지로 이동합니다...")
                page.goto(urls['업무포털 메인'])
        
            page.wait_for_load_state('networkidle')
        
        # 페이지 URL이 로그인 페이지가 맞는지 한번 더 확인하고, 아니라면 이동
        if urls['업무포털 로그인'] not in page.url:
            page.goto(urls['업무포털 로그인'])
            page.wait_for_load_state('networkidle')
        # --- [수정 로직 끝] ---

        print("로그인을 시작합니다.")
        login(page)
        _wait_for_login_success(page)
        
        # 팝업 처리
        try:
            dont_show_today_checkbox = page.get_by_label("오늘하루 이창 열지 않기", exact=True)
            dont_show_today_checkbox.wait_for(state='visible', timeout=5000)
            dont_show_today_checkbox.check()
            close_button = page.get_by_role("button", name="닫기", exact=True)
            close_button.click()
        except TimeoutError:
            print("로그인 후 팝업창이 없거나 관련 요소를 찾지 못해 넘어갑니다.")
        
        app_instance.add_log("업무포털 로그인이 완료되었습니다.")
        app_instance.after(0, lambda: messagebox.showinfo("성공", "로그인이 완료되었습니다."))
        return True

    except Exception as e:
        _handle_error(e, app_instance)
        return False

def neis_attendace(app_instance):
    """나이스 출결관리 메뉴로 이동"""
    try:
        page = _navigate_to_neis(app_instance)
        
        neis_go_menu(page, '학급담임', '학적', '출결관리', '출결관리')
        neis_click_btn(page, '조회')
        app_instance.add_log("나이스 출결관리 메뉴로 이동하여 조회를 클릭했습니다.")
        app_instance.after(0, lambda: messagebox.showinfo("완료", "나이스 출결관리 메뉴로 이동하여 조회를 클릭했습니다."))
    except Exception as e:
        _handle_error(e, app_instance)

def neis_haengteuk(app_instance):
    """행동특성 및 종합의견 입력"""
    try:
        page = _navigate_to_neis(app_instance)

        data = get_excel_data()
        if data is None:
            app_instance.add_log("엑셀 파일을 선택하지 않아 작업을 취소합니다.")
            app_instance.after(0, lambda: messagebox.showwarning("취소", "엑셀 파일을 선택하지 않아 작업을 취소합니다."))
            return

        neis_go_menu(page, '학급담임', '학생생활', '행동특성및종합의견', '행동특성및종합의견')
        neis_click_btn(page, '조회')

        total_student_cnt = int(page.locator('span.fw-medium').inner_text())
        done = set()
        
        app_instance.add_log("행동특성 입력을 시작합니다. 첫 번째 학생을 클릭해주세요.")
        app_instance.after(0, lambda: messagebox.showinfo("시작", "지금부터 행동특성 입력을 시작합니다.\n첫 번째 학생을 클릭해주세요."))

        while len(done) < total_student_cnt:
            done = neis_fill_row(page, done, data, '내용', 'div.cl-control.cl-default-cell')

        neis_click_btn(page, '저장')
        app_instance.add_log("행동특성 및 종합의견 입력 및 저장을 완료했습니다.")
        app_instance.after(0, lambda: messagebox.showinfo("완료", "행동특성 및 종합의견 입력 및 저장을 완료했습니다."))
    except Exception as e:
        _handle_error(e, app_instance)

def neis_hakjjong(app_instance):
    """학기말 종합의견(담임) 메뉴로 이동"""
    try:
        page = _navigate_to_neis(app_instance)
        
        neis_go_menu(page, '학급담임', '성적', '학생평가', '학기말종합의견')
        app_instance.add_log("학기말 종합의견(담임) 메뉴로 이동했습니다.")
        app_instance.after(0, lambda: messagebox.showinfo("완료", "학기말 종합의견(담임) 메뉴로 이동했습니다."))
    except Exception as e:
        _handle_error(e, app_instance)

def neis_class_hakjjong(app_instance):
    """학기말 종합의견(교과) 메뉴로 이동"""
    try:
        page = _navigate_to_neis(app_instance)
        
        neis_go_menu(page, '교과담임', '성적', '학생평가', '학기말종합의견')
        app_instance.add_log("학기말 종합의견(교과) 메뉴로 이동했습니다.")
        app_instance.after(0, lambda: messagebox.showinfo("완료", "학기말 종합의견(교과) 메뉴로 이동했습니다."))
    except Exception as e:
        _handle_error(e, app_instance)


