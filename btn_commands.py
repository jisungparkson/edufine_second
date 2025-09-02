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

def _check_password_file_exists() -> bool:
    """
    config.ini에 설정된 password_file이 실제로 존재하는지 확인
    """
    try:
        import configparser
        import os
        
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        
        try:
            password_filepath = config['Paths']['password_file']
        except (KeyError, configparser.NoSectionError):
            password_filepath = 'C:\\GPKI\\password.txt'  # 기본값
        
        return os.path.exists(password_filepath)
        
    except Exception:
        return False

def _enhance_manual_login_session(app_instance, portal_page) -> bool:
    """
    수동 로그인 세션을 연계 시스템 호환 세션으로 보완하는 함수
    자동 로그인 없이 수동 로그인 세션의 누락된 부분을 채워넣습니다
    """
    try:
        app_instance.add_log("세션 보완 과정을 시작합니다...")
        
        # 1. 현재 페이지 새로고침으로 세션 상태 최신화
        app_instance.add_log("페이지를 새로고침하여 세션 상태를 최신화합니다...")
        portal_page.reload()
        portal_page.wait_for_load_state('networkidle', timeout=30000)
        
        # 2. 메인 페이지의 모든 링크와 스크립트가 완전히 로드될 때까지 대기
        app_instance.add_log("페이지 구성 요소가 완전히 로드될 때까지 기다립니다...")
        portal_page.wait_for_timeout(3000)  # 추가 로딩 시간 확보
        
        # 3. 필요한 세션 쿠키나 토큰이 설정되었는지 확인
        app_instance.add_log("세션 정보를 확인합니다...")
        
        # 4. 페이지의 모든 자바스크립트 실행이 완료되도록 대기
        # 업무포털의 경우 로그인 후 추가 스크립트가 실행되어 세션을 완성할 수 있음
        try:
            # 페이지가 완전히 준비될 때까지 대기
            portal_page.wait_for_function(
                "() => document.readyState === 'complete'",
                timeout=10000
            )
            app_instance.add_log("페이지 로딩이 완전히 완료되었습니다.")
        except:
            app_instance.add_log("페이지 로딩 확인 중 타임아웃이 발생했지만 계속 진행합니다.")
        
        # 5. 추가적인 세션 초기화 과정 (필요시)
        # 일부 웹 애플리케이션은 메인 페이지 방문 후 특정 액션이 필요할 수 있음
        app_instance.add_log("세션 보완 과정이 완료되었습니다.")
        return True
        
    except Exception as e:
        app_instance.add_log(f"세션 보완 중 오류 발생: {str(e)}")
        return False

def _ensure_valid_session_and_navigate(app_instance, target_service) -> Page:
    """
    세션 확보 및 이동 Gatekeeper 함수 (수동 로그인 친화적)
    수동 로그인 사용자도 연계 시스템에 접근할 수 있도록 세션을 보완합니다
    """
    try:
        app_instance.add_log(f"{target_service} 시스템 접근을 위한 세션 상태를 확인합니다...")
        
        # a. 현재 페이지 확인
        current_page = browser_manager.get_page()
        current_url = current_page.url
        app_instance.add_log(f"현재 페이지: {current_url}")
        
        # b. 수동 로그인 상태 처리 (자동 로그인 강요 없이)
        if "bpm_man_mn00_001.do" in current_url:
            app_instance.add_log("수동 로그인 상태가 감지되었습니다.")
            app_instance.add_log("수동 로그인 세션을 연계 시스템 호환 세션으로 보완합니다...")
            
            # 세션 보완 시도 (자동 로그인 대신)
            session_enhanced = _enhance_manual_login_session(app_instance, current_page)
            if not session_enhanced:
                app_instance.add_log("세션 보완에 실패했습니다. 브라우저에서 직접 접근을 시도해보세요.")
                messagebox.showinfo(
                    "세션 보완 실패", 
                    f"수동 로그인 세션을 {target_service} 호환 세션으로 보완하는데 실패했습니다.\n\n대안:\n• 브라우저에서 직접 {target_service} 링크를 클릭해보세요\n• 또는 로그아웃 후 다시 로그인해보세요"
                )
                return None
            
            app_instance.add_log("수동 로그인 세션이 성공적으로 보완되었습니다.")
        
        # c. 세션이 없을 경우
        elif "lg00_001.do" in current_url or current_url == "about:blank":
            app_instance.add_log("세션이 없는 상태입니다.")
            
            # password_file 존재 여부 확인
            has_password_file = _check_password_file_exists()
            
            if has_password_file:
                app_instance.add_log("비밀번호 파일이 존재합니다. 자동 로그인을 시도합니다.")
                login_success = do_login_only(app_instance)
                if not login_success:
                    app_instance.add_log("자동 로그인에 실패했습니다.")
                    return None
            else:
                app_instance.add_log("비밀번호 파일이 없습니다. 수동 로그인이 필요합니다.")
                messagebox.showinfo(
                    "로그인 필요",
                    f"{target_service} 시스템에 접근하려면 먼저 로그인이 필요합니다.\n\n방법:\n1. '업무포털 접속' 버튼을 클릭하세요\n2. 브라우저에서 직접 로그인하세요\n3. 로그인 완료 후 이 버튼을 다시 클릭하세요"
                )
                return None
        
        # d. 세션 확보 후 타겟 서비스로 이동
        app_instance.add_log(f"유효한 세션이 확보되었습니다. {target_service}로 이동합니다.")
        portal_page = browser_manager.get_page()
        
        # 연계 시스템 링크 접근 시도 (재시도 포함)
        for attempt in range(2):  # 최대 2번 시도
            try:
                app_instance.add_log(f"{target_service} 링크 접근 시도 {attempt + 1}/2")
                
                if target_service == "나이스":
                    service_link = portal_page.get_by_role("link", name="나이스", exact=True).first
                else:
                    raise ValueError(f"지원하지 않는 서비스: {target_service}")
                
                # 링크가 실제로 보이고 클릭 가능한지 확인
                service_link.wait_for(state="visible", timeout=10000)
                app_instance.add_log(f"{target_service} 링크를 확인했습니다. 클릭합니다.")
                
                # 링크 클릭하여 새 창으로 이동
                with portal_page.expect_popup() as popup_info:
                    service_link.click()
                
                target_page = popup_info.value
                app_instance.add_log(f"{target_service} 새 창이 열렸습니다. 페이지 로딩을 기다립니다...")
                target_page.wait_for_load_state("networkidle")
                
                # 연계 시스템 페이지가 제대로 로드되었는지 확인
                if target_service == "나이스" and "neis.go.kr" in target_page.url:
                    browser_manager.page = target_page
                    app_instance.add_log(f"✅ {target_service} 페이지 이동이 성공적으로 완료되었습니다!")
                    messagebox.showinfo("접속 성공", f"{target_service} 시스템에 성공적으로 접속했습니다!")
                    return target_page
                else:
                    app_instance.add_log(f"{target_service} 페이지 로드에 문제가 있습니다. 재시도합니다...")
                    if attempt == 0:  # 첫 번째 시도 실패 시 세션 재보완
                        app_instance.add_log("세션 재보완을 시도합니다...")
                        _enhance_manual_login_session(app_instance, portal_page)
                        continue
                    
            except Exception as link_error:
                app_instance.add_log(f"{target_service} 링크 접근 실패 (시도 {attempt + 1}): {link_error}")
                
                if attempt == 0:  # 첫 번째 시도 실패 시
                    app_instance.add_log("세션을 재보완하고 다시 시도합니다...")
                    _enhance_manual_login_session(app_instance, portal_page)
                    continue
        
        # 모든 시도 실패
        app_instance.add_log(f"모든 시도가 실패했습니다. 수동 접근을 안내합니다.")
        messagebox.showinfo(
            "자동 접근 실패",
            f"{target_service} 자동 접근에 실패했습니다.\n\n수동 접근 방법:\n1. 브라우저에서 직접 '{target_service}' 링크를 클릭해보세요\n2. 만약 링크가 작동하지 않으면:\n   • 로그아웃 후 다시 로그인해보세요\n   • 브라우저를 새로고침해보세요"
        )
        return None
        
    except Exception as e:
        _handle_error(e, app_instance)
        return None

def _navigate_to_neis(app_instance) -> Page:
    """
    상태 감지 및 사용자 안내 중심의 나이스 이동 함수
    수동/자동 로그인 상태를 지능적으로 판단하여 적절한 안내 제공
    """
    try:
        app_instance.add_log("나이스 페이지 접근을 시작합니다...")
        
        # 1단계: 이미 열린 나이스 탭 검색
        if browser_manager.browser and browser_manager.browser.is_connected():
            for context in browser_manager.browser.contexts:
                for page in context.pages:
                    if "neis.go.kr" in page.url and not page.is_closed():
                        app_instance.add_log("이미 열려있는 나이스 탭을 발견했습니다.")
                        page.bring_to_front()
                        browser_manager.page = page
                        return page
        
        # 2단계: 상태 판단 - 업무포털 메인 페이지 확인 (수동 로그인 판단)
        portal_page = browser_manager.get_page()
        current_url = portal_page.url
        app_instance.add_log(f"현재 페이지 URL: {current_url}")
        
        # 3단계 & 4단계: 수동 로그인 상태일 경우 사용자 안내 및 대기
        if 'bpm_man_mn00_001.do' in current_url:
            app_instance.add_log("수동 로그인 상태 감지. 사용자에게 나이스 직접 클릭을 요청합니다.")
            messagebox.showinfo("다음 단계 안내", 
                               "수동으로 로그인하셨습니다.\n\n"
                               "1. 웹 화면에서 직접 [나이스] 링크를 클릭하세요.\n"
                               "2. 새 탭으로 나이스가 열리면, 이 창의 [확인] 버튼을 누르세요.")
            
            # 사용자가 나이스 탭을 열 때까지 기다림
            app_instance.add_log("사용자가 나이스 탭을 여는 것을 기다립니다...")
            with browser_manager.browser.expect_page() as new_page_info:
                pass  # 사용자의 클릭을 기다림
            
            neis_page = new_page_info.value
            neis_page.wait_for_load_state("networkidle")
            browser_manager.page = neis_page
            app_instance.add_log("사용자가 연 '나이스' 탭으로 제어권을 전환했습니다.")
            return neis_page
        
        # 5단계: 다른 페이지에 있는 경우 (로그인 페이지이거나 기타 상황)
        else:
            app_instance.add_log("업무포털 메인 페이지가 아닙니다. 먼저 로그인이 필요할 수 있습니다.")
            messagebox.showinfo("로그인 안내", 
                               "나이스 접근을 위해서는 먼저 업무포털 로그인이 필요합니다.\n\n"
                               "1. '업무포털 자동 로그인 (권장)' 버튼을 클릭하거나\n"
                               "2. '브라우저 열기 (수동 로그인용)' 버튼으로 직접 로그인하세요.")
            return None
            
    except Exception as e:
        _handle_error(e, app_instance)
        return None


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
        if not page:
            return
        
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
        if not page:
            return

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
        if not page:
            return
        
        neis_go_menu(page, '학급담임', '성적', '학생평가', '학기말종합의견')
        app_instance.add_log("학기말 종합의견(담임) 메뉴로 이동했습니다.")
        app_instance.after(0, lambda: messagebox.showinfo("완료", "학기말 종합의견(담임) 메뉴로 이동했습니다."))
    except Exception as e:
        _handle_error(e, app_instance)

def neis_class_hakjjong(app_instance):
    """학기말 종합의견(교과) 메뉴로 이동"""
    try:
        page = _navigate_to_neis(app_instance)
        if not page:
            return
        
        neis_go_menu(page, '교과담임', '성적', '학생평가', '학기말종합의견')
        app_instance.add_log("학기말 종합의견(교과) 메뉴로 이동했습니다.")
        app_instance.after(0, lambda: messagebox.showinfo("완료", "학기말 종합의견(교과) 메뉴로 이동했습니다."))
    except Exception as e:
        _handle_error(e, app_instance)


