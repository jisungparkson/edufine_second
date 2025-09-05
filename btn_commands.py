# btn_commands.py (공유 영구 세션 아키텍처 버전)

from playwright.sync_api import sync_playwright, Page, Playwright, Browser, BrowserContext, TimeoutError, expect
from utils import urls
from tkinter import messagebox


class BrowserManager:
    """
    공유 영구 세션을 관리하는 중앙 허브
    단 한 번의 로그인으로 모든 서비스를 병렬 관리
    """
    def __init__(self):
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.pages = {}  # {'나이스': Page, '에듀파인': Page}
        self.is_logged_in = False  # 로그인 상태 플래그
        self.is_closing = False  # 종료 상태 플래그
        print("BrowserManager(세션 관리자)가 준비되었습니다.")

    def set_closing_flag(self):
        """프로그램 종료가 시작되었음을 알립니다."""
        self.is_closing = True
        print("BrowserManager: 프로그램 종료 플래그가 설정되었습니다.")

    def ensure_browser_initialized(self):
        """
        지연 초기화: 첫 번째 자동화 버튼이 클릭될 때만 브라우저를 시작
        """
        if self.browser is None or not self.browser.is_connected():
            print("브라우저를 지연 초기화합니다...")
            
            if self.playwright is None:
                self.playwright = sync_playwright().start()
            
            # 새 브라우저 실행
            self.browser = self.playwright.chromium.launch(
                headless=False, 
                channel="msedge"
            )
            print("새 Edge 브라우저를 실행했습니다.")
            
            # 단일 컨텍스트 생성 (모든 페이지가 쿠키와 세션을 공유)
            self.context = self.browser.new_context()
            print("공유 브라우저 컨텍스트를 생성했습니다.")

    def get_or_create_page(self, service_name: str) -> Page:
        """
        서비스별 페이지를 가져오거나 새로 생성
        기존 페이지가 있으면 재사용, 없으면 새로 생성
        """
        self.ensure_browser_initialized()
        
        # 기존 페이지가 있고 유효하면 재사용
        if service_name in self.pages:
            page = self.pages[service_name]
            if not page.is_closed():
                page.bring_to_front()
                return page
        
        # 새 페이지 생성 (공유 컨텍스트를 통해)
        page = self.context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        self.pages[service_name] = page
        print(f"{service_name} 전용 새 페이지를 생성했습니다.")
        
        return page

    def close(self):
        """모든 리소스를 안전하게 종료합니다."""
        try:
            if self.browser and self.browser.is_connected():
                print("공유 브라우저를 닫습니다.")
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
            self.context = None
            self.pages = {}
            self.is_logged_in = False


# 단 하나의 세션 관리자 인스턴스 생성
browser_manager = BrowserManager()


def _handle_error(e):
    """오류 처리 시, 세션 관리자를 통해 안전하게 모든 것을 종료합니다."""
    if browser_manager.is_closing:
        print("프로그램 종료 중 발생한 예상된 오류입니다. 무시합니다.")
        return
    
    error_message = f"{type(e).__name__}: {e}"
    messagebox.showerror("오류 발생", error_message)
    browser_manager.close()


def _perform_universal_login(app_instance):
    """
    범용 로그인 워크플로우: 단 한 번의 로그인으로 모든 서비스의 관문 역할
    이미 로그인되어 있으면 아무것도 하지 않고 바로 반환
    """
    # 이미 로그인되어 있으면 스킵
    if browser_manager.is_logged_in:
        print("✓ 이미 로그인되어 있습니다. 범용 로그인을 건너뜁니다.")
        return
    
    try:
        print("=== 범용 로그인 워크플로우 시작 ===")
        browser_manager.ensure_browser_initialized()
        
        # 임시 로그인용 페이지 생성
        login_page = browser_manager.context.new_page()
        login_page.set_viewport_size({"width": 1920, "height": 1080})
        
        # 1단계: 업무포털 로그인 페이지로 이동
        print("1단계: 업무포털 로그인 페이지로 이동합니다...")
        login_page.goto(urls['업무포털 로그인'])
        login_page.wait_for_load_state("networkidle", timeout=30000)
        
        # 2단계: 사용자 수동 로그인 안내
        print("2단계: 사용자 수동 로그인 안내...")
        messagebox.showinfo("통합 로그인 안내", 
                          "모든 서비스 이용을 위한 통합 로그인이 필요합니다. 🔐\n\n"
                          "브라우저에서 수동으로 로그인을 완료해주세요.\n"
                          "로그인 완료 후 자동으로 감지됩니다.\n\n"
                          "이 창에서 '확인'을 클릭하고 브라우저에서 로그인해주세요.")
        
        # 3단계: 로그인 성공 감지
        print("3단계: 로그인 성공을 감지합니다...")
        try:
            # 로그인 페이지에서 벗어나면 로그인 성공으로 판단
            login_page.wait_for_function(
                "() => !window.location.href.includes('bpm_lgn_lg00_001.do')", 
                timeout=180000
            )
            print("✓ 로그인 성공이 감지되었습니다!")
            
        except TimeoutError:
            current_url = login_page.url
            if 'lg00_001.do' not in current_url:
                print("✓ 로그인이 완료된 것으로 판단됩니다.")
            else:
                raise TimeoutError("로그인 시간이 초과되었습니다. 다시 시도해주세요.")
        
        # 4단계: 로그인 상태 플래그 설정
        browser_manager.is_logged_in = True
        print("✓ 통합 로그인이 완료되었습니다! 이제 모든 서비스를 사용할 수 있습니다.")
        
        # 로그인용 페이지 닫기
        login_page.close()
        
    except Exception as e:
        print(f"범용 로그인 워크플로우 중 오류: {e}")
        raise


def navigate_to_neis(app_instance):
    """
    나이스 페이지 관리 함수:
    범용 로그인 확인 후 나이스 전용 페이지를 열거나 활성화
    """
    try:
        print("=== 나이스 페이지 관리 시작 ===")
        
        # 1단계: 범용 로그인 보장
        _perform_universal_login(app_instance)
        
        # 2단계: 나이스 페이지 가져오기 또는 생성
        page = browser_manager.get_or_create_page('나이스')
        
        # 3단계: 나이스 URL로 이동 (이미 로그인되어 있으므로 자동 접속)
        print("나이스 사이트로 이동합니다...")
        page.goto(urls['나이스'])
        page.wait_for_load_state("networkidle", timeout=30000)
        
        # 4단계: 접속 완료 안내
        current_url = page.url
        if 'neis.go.kr' in current_url:
            print("✓ 나이스에 성공적으로 접속했습니다!")
            messagebox.showinfo("나이스 접속 완료", 
                              "나이스에 성공적으로 접속했습니다! 🎉\n\n"
                              "이제 나이스에서 필요한 작업을 수행하세요.\n"
                              "다른 서비스도 동일한 세션으로 접속 가능합니다.")
        else:
            print("나이스 접속 중... 추가 리디렉션이 진행될 수 있습니다.")
            messagebox.showinfo("나이스 접속 중", 
                              "나이스 접속이 진행 중입니다.\n\n"
                              "잠시 후 나이스 페이지가 로드됩니다.")
        
    except Exception as e:
        print(f"나이스 접속 중 오류: {e}")
        _handle_error(e)


def navigate_to_edufine(app_instance):
    """
    K-에듀파인 페이지 관리 함수:
    범용 로그인 확인 후 K-에듀파인 전용 페이지를 열거나 활성화
    """
    try:
        print("=== K-에듀파인 페이지 관리 시작 ===")
        
        # 1단계: 범용 로그인 보장
        _perform_universal_login(app_instance)
        
        # 2단계: K-에듀파인 페이지 가져오기 또는 생성
        page = browser_manager.get_or_create_page('에듀파인')
        
        # 3단계: K-에듀파인 URL로 이동 (이미 로그인되어 있으므로 자동 접속)
        print("K-에듀파인 사이트로 이동합니다...")
        page.goto(urls['에듀파인'])
        page.wait_for_load_state("networkidle", timeout=30000)
        
        # 4단계: 접속 완료 안내
        current_url = page.url
        if 'klef.jbe.go.kr' in current_url:
            print("✓ K-에듀파인에 성공적으로 접속했습니다!")
            messagebox.showinfo("K-에듀파인 접속 완료", 
                              "K-에듀파인에 성공적으로 접속했습니다! 🎉\n\n"
                              "이제 K-에듀파인에서 필요한 작업을 수행하세요.\n"
                              "다른 서비스도 동일한 세션으로 접속 가능합니다.")
        else:
            print("K-에듀파인 접속 중... 추가 리디렉션이 진행될 수 있습니다.")
            messagebox.showinfo("K-에듀파인 접속 중", 
                              "K-에듀파인 접속이 진행 중입니다.\n\n"
                              "잠시 후 K-에듀파인 페이지가 로드됩니다.")
        
    except Exception as e:
        print(f"K-에듀파인 접속 중 오류: {e}")
        _handle_error(e)