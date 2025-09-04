# btn_commands.py (Sync API 통일 버전)

from playwright.sync_api import sync_playwright, Page, Playwright, Browser, TimeoutError, expect
from utils import (
    urls, login, neis_go_menu, neis_click_btn, switch_tab, open_url_in_new_tab
)
from tkinter import messagebox

class BrowserManager:
    """Playwright의 브라우저 상태를 총괄 관리하는 클래스"""
    def __init__(self):
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.page: Page = None
        self.debug_port = 9222
        print("BrowserManager가 준비되었습니다.")

    def get_page(self) -> Page:
        """
        기존 Edge 디버그 브라우저에 연결을 우선 시도하고, 
        실패 시 새 브라우저를 시작하는 스마트 연결 시스템
        """
        # 1. Playwright 인스턴스 확인
        if self.playwright is None:
            print("Playwright 인스턴스를 시작합니다.")
            self.playwright = sync_playwright().start()

        # 2. 기존 브라우저가 연결되어 있고 유효하면 그대로 사용
        if self.browser and self.browser.is_connected():
            if self.page and not self.page.is_closed():
                return self.page

        # 3. Edge 디버그 모드에 연결 시도 (사용자가 수동 로그인한 브라우저)
        try:
            print(f"포트 {self.debug_port}에서 기존 Edge 브라우저 연결을 시도합니다...")
            self.browser = self.playwright.chromium.connect_over_cdp(f"http://localhost:{self.debug_port}")
            print("기존 Edge 브라우저에 성공적으로 연결되었습니다!")
            
            # 기존 페이지 중 업무포털 관련 페이지 찾기
            portal_page = self._find_portal_page()
            if portal_page:
                print("기존 업무포털 페이지를 찾았습니다.")
                self.page = portal_page
                return self.page
            
        except Exception as e:
            print(f"기존 브라우저 연결 실패: {e}")

        # 4. 연결 실패 시 새 브라우저 시작
        try:
            print("새 Edge 브라우저를 시작합니다...")
            self.browser = self.playwright.chromium.launch(
                headless=False, 
                channel="msedge",
                args=[f"--remote-debugging-port={self.debug_port}"]
            )
        except Exception as e:
            print(f"디버그 포트로 브라우저 시작 실패, 일반 모드로 시도: {e}")
            self.browser = self.playwright.chromium.launch(headless=False, channel="msedge")

        # 5. 페이지 생성
        if self.page is None or self.page.is_closed():
            print("새 페이지를 생성합니다.")
            if len(self.browser.contexts) > 0:
                self.page = self.browser.contexts[0].new_page()
            else:
                context = self.browser.new_context()
                self.page = context.new_page()
            
            self.page.set_viewport_size({"width": 1920, "height": 1080})

        return self.page

    def _find_portal_page(self) -> Page:
        """기존 브라우저에서 업무포털 관련 페이지를 찾습니다."""
        try:
            for context in self.browser.contexts:
                for page in context.pages:
                    url = page.url
                    if any(domain in url for domain in ['eduptl.kr', 'neis.go.kr', 'klef.jbe.go.kr']):
                        print(f"업무포털 관련 페이지 발견: {url}")
                        return page
        except Exception as e:
            print(f"기존 페이지 검색 중 오류: {e}")
        return None

    def ensure_valid_connection(self) -> Page:
        """
        자동화 함수 실행 전 브라우저 연결 상태를 검증하고 복구합니다.
        """
        try:
            if self.page and not self.page.is_closed():
                # 페이지가 응답하는지 테스트
                self.page.evaluate("() => document.readyState")
                return self.page
        except Exception as e:
            print(f"기존 페이지 연결 끊어짐, 재연결 시도: {e}")
        
        # 연결이 끊어졌으면 재연결
        return self.get_page()

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

def _handle_error(e):
    """오류 처리 시, 현장 감독을 통해 안전하게 모든 것을 종료합니다."""
    error_message = f"{type(e).__name__}: {e}"
    messagebox.showerror("오류 발생", error_message)
    browser_manager.close()

def _navigate_to_neis() -> Page:
    """업무포털에 로그인하고, '나이스' 버튼을 클릭하여 새 탭으로 열린 나이스 페이지를 반환합니다."""
    print("업무포털에 접속하여 나이스로 이동을 시작합니다.")
    
    # 브라우저 연결 상태 검증 및 복구
    portal_page = browser_manager.ensure_valid_connection()
    
    # 업무포털에 로그인되어 있는지 확인
    current_url = portal_page.url
    if 'lg00_001.do' in current_url:
        print("로그인이 필요합니다. 로그인을 진행합니다.")
        open_eduptl()
        portal_page = browser_manager.get_page()
    elif 'eduptl.kr' not in current_url:
        print("업무포털이 아닙니다. 업무포털로 이동합니다.")
        portal_page.goto(urls['업무포털 메인'])
        portal_page.wait_for_load_state("networkidle", timeout=30000)
    
    # 나이스 링크 클릭하여 새 탭 열기
    with portal_page.expect_popup(timeout=30000) as popup_info:
        print("업무포털 메인 화면에서 '나이스' 링크를 클릭합니다...")
        neis_link = portal_page.get_by_role("link", name="나이스", exact=True).first
        neis_link.wait_for(state="visible", timeout=30000)
        neis_link.click()
    
    neis_page = popup_info.value
    print("새 탭에서 나이스 페이지가 열렸습니다. 로딩을 기다립니다...")
    neis_page.wait_for_load_state("networkidle", timeout=30000)
    browser_manager.page = neis_page
    return neis_page

def _wait_for_login_success(page: Page):
    """로그인이 성공했는지 확인하는 공통 함수"""
    print("로그인 성공 확인 중... (페이지 로딩 대기)")
    
    try:
        # 페이지 로딩 완료 대기 (견고한 조건)
        page.wait_for_load_state('networkidle', timeout=30000)
        
        current_url = page.url
        print(f"현재 URL: {current_url}")
        
        # 로그인 페이지에서 벗어났는지 확인
        if 'lg00_001.do' not in current_url:
            # 추가 검증: 메인 페이지의 특정 요소가 로드되었는지 확인
            try:
                page.wait_for_selector('a[href*="neis"]', timeout=10000)
                print("로그인 성공 (URL 및 페이지 요소 확인)")
                return
            except:
                print("메인 페이지 요소 로드 대기 중...")
        
        # 간단한 대기 후 재확인 (견고한 재시도)
        for i in range(3):
            page.wait_for_timeout(3000)
            current_url = page.url
            if 'lg00_001.do' not in current_url:
                try:
                    page.wait_for_selector('a[href*="neis"]', timeout=5000)
                    print(f"로그인 성공 (재확인 {i+1}회차)")
                    return
                except:
                    continue
        
        print("로그인이 완료되지 않았습니다. 수동으로 로그인을 완료해주세요.")
        messagebox.showinfo("수동 로그인 안내", 
                          "브라우저에서 수동으로 로그인을 완료해주세요.\n"
                          "로그인 완료 후 이 창에서 '확인'을 눌러주세요.\n\n"
                          "※ 프로그램이 브라우저 상태를 지속적으로 확인하고 있습니다.")
        
        # 사용자가 수동 로그인 완료할 때까지 스마트 대기
        retry_count = 0
        max_retries = 300  # 5분 최대 대기
        
        while 'lg00_001.do' in page.url and retry_count < max_retries:
            try:
                page.wait_for_timeout(1000)
                # 페이지 응답성 확인
                page.evaluate("() => document.readyState")
                retry_count += 1
                
                # 30초마다 상태 체크 메시지
                if retry_count % 30 == 0:
                    print(f"수동 로그인 대기 중... ({retry_count}초 경과)")
                    
            except Exception as e:
                print(f"페이지 상태 확인 중 오류, 재연결 시도: {e}")
                page = browser_manager.ensure_valid_connection()
        
        if retry_count >= max_retries:
            raise TimeoutError("수동 로그인 대기 시간이 초과되었습니다.")
        
        # 최종 검증
        page.wait_for_load_state('networkidle', timeout=10000)
        print("수동 로그인 완료 확인됨")
        
    except Exception as e:
        print(f"로그인 확인 중 오류: {e}")
        messagebox.showerror("로그인 오류", f"로그인 확인 중 오류가 발생했습니다: {e}")
        raise

def open_eduptl():
    """
    업무포털 '로그인' 페이지로 직접 이동합니다.
    사용자의 수동 로그인이 완료될 때까지 기다립니다.
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
        
        # 사용자의 수동 로그인 완료를 기다립니다.
        _wait_for_login_success(page)
        
    except Exception as e:
        _handle_error(e) # 오류 발생 시 처리

def do_login_only():
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
        
        messagebox.showinfo("성공", "로그인이 완료되었습니다.")

    except Exception as e:
        _handle_error(e)

def neis_class_hakjjong():
    """학기말 종합의견(교과) 메뉴로 이동"""
    try:
        page = _navigate_to_neis()
             
        neis_go_menu(page, '교과담임', '성적', '학생평가', '학기말종합의견')
        messagebox.showinfo("완료", "학기말 종합의견(교과) 메뉴로 이동했습니다.")
    except Exception as e:
        _handle_error(e)