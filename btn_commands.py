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
        """현재 사용 가능한, 유효한 페이지 객체를 반환합니다."""
        # 1. 플레이라이트 자체가 시작되지 않았다면, 기존 브라우저 연결 시도
        if self.playwright is None:
            print("Playwright 인스턴스를 시작합니다.")
            self.playwright = sync_playwright().start()
            
            # 기존 Edge 브라우저에 연결 시도
            try:
                print("기존 Edge 브라우저에 연결을 시도합니다...")
                self.browser = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
                print("기존 브라우저에 성공적으로 연결되었습니다!")
                
                # 기존 탭 중에서 업무포털 관련 페이지 찾기
                for context in self.browser.contexts:
                    for page in context.pages:
                        try:
                            if 'eduptl' in page.url or 'neis' in page.url or '업무포털' in page.title():
                                print(f"기존 페이지를 사용합니다: {page.title()}")
                                self.page = page
                                page.bring_to_front()
                                return self.page
                        except:
                            continue
                
                # 기존 페이지가 없으면 새 페이지 생성
                if len(self.browser.contexts) > 0:
                    self.page = self.browser.contexts[0].new_page()
                else:
                    context = self.browser.new_context()
                    self.page = context.new_page()
                    
            except Exception as e:
                print(f"기존 브라우저 연결 실패: {e}")
                print("새 브라우저를 시작합니다.")
                self.browser = self.playwright.chromium.launch(headless=False, channel="msedge")
        
        # 2. 브라우저가 꺼졌다면, 다시 연결 시도 후 새로 켭니다.
        if not self.browser.is_connected():
            print("브라우저 연결이 끊어져 재연결을 시도합니다.")
            try:
                self.browser = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
                print("기존 브라우저에 재연결되었습니다!")
            except:
                print("재연결 실패, 새 브라우저를 시작합니다.")
                self.browser = self.playwright.chromium.launch(headless=False, channel="msedge")

        # 3. 페이지가 없거나 닫혔다면, 새로 만듭니다.
        if self.page is None or self.page.is_closed():
            print("페이지가 닫혀있어 새로 생성합니다.")
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

def _handle_error(e):
    """오류 처리 시, 현장 감독을 통해 안전하게 모든 것을 종료합니다."""
    error_message = f"{type(e).__name__}: {e}"
    messagebox.showerror("오류 발생", error_message)
    browser_manager.close()

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

def open_eduptl():
    """업무포털 페이지 접속, 로그인 및 팝업 처리"""
    try:
        page = browser_manager.get_page()
        
        # 이미 업무포털에 로그인되어 있는지 확인
        if '업무포털' in page.title() and not page.url.endswith('lg00_001.do'):
            page.bring_to_front()
            return
            
        page.goto(urls['업무포털 메인'])
        if page.url == urls['업무포털 로그인']:
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
            print("팝업창이 없거나 관련 요소를 찾지 못해 넘어갑니다.")

    except Exception as e:
        _handle_error(e)

def do_login_only():
    """현재 페이지가 로그인 페이지일 경우에만 로그인을 수행하는 함수"""
    try:
        page = browser_manager.get_page()

        # 현재 페이지 URL 확인
        current_url = page.url
        print(f"현재 페이지 URL: {current_url}")
        
        # 업무포털 메인 페이지로 이동
        if not current_url.startswith('https://jbe.eduptl.kr'):
            page.goto(urls['업무포털 메인'])
            page.wait_for_load_state('networkidle')
            current_url = page.url
            print(f"이동 후 URL: {current_url}")

        # 로그인 페이지가 아니면 경고
        if current_url != urls['업무포털 로그인']:
            messagebox.showwarning("경고", "이 기능은 업무포털 로그인 화면에서만 사용할 수 있습니다.")
            page.bring_to_front()
            return

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
            print("팝업창이 없거나 관련 요소를 찾지 못해 넘어갑니다.")
        
        messagebox.showinfo("성공", "로그인이 완료되었습니다.")

    except Exception as e:
        _handle_error(e)

def neis_attendace():
    """나이스 출결관리 메뉴로 이동"""
    try:
        # 업무포털 먼저 접속하여 기존 창 확보
        open_eduptl()
        
        # 현재 업무포털 페이지에서 나이스 URL로 이동
        page = browser_manager.get_page()
        page.goto(urls['나이스'])
        
        neis_go_menu(page, '학급담임', '학적', '출결관리', '출결관리')
        neis_click_btn(page, '조회')
        messagebox.showinfo("완료", "나이스 출결관리 메뉴로 이동하여 조회를 클릭했습니다.")
    except Exception as e:
        _handle_error(e)

def neis_haengteuk():
    """행동특성 및 종합의견 입력"""
    try:
        # 업무포털 먼저 접속하여 기존 창 확보
        open_eduptl()
        
        # 현재 업무포털 페이지에서 나이스 URL로 이동
        page = browser_manager.get_page()
        page.goto(urls['나이스'])

        data = get_excel_data()
        if data is None:
            messagebox.showwarning("취소", "엑셀 파일을 선택하지 않아 작업을 취소합니다.")
            return

        neis_go_menu(page, '학급담임', '학생생활', '행동특성및종합의견', '행동특성및종합의견')
        neis_click_btn(page, '조회')

        total_student_cnt = int(page.locator('span.fw-medium').inner_text())
        done = set()
        
        messagebox.showinfo("시작", "지금부터 행동특성 입력을 시작합니다.\n첫 번째 학생을 클릭해주세요.")

        while len(done) < total_student_cnt:
            done = neis_fill_row(page, done, data, '내용', 'div.cl-control.cl-default-cell')

        neis_click_btn(page, '저장')
        messagebox.showinfo("완료", "행동특성 및 종합의견 입력 및 저장을 완료했습니다.")
    except Exception as e:
        _handle_error(e)

def neis_hakjjong():
    """학기말 종합의견(담임) 메뉴로 이동"""
    try:
        # 업무포털 먼저 접속하여 기존 창 확보
        open_eduptl()
        
        # 현재 업무포털 페이지에서 나이스 URL로 이동
        page = browser_manager.get_page()
        page.goto(urls['나이스'])
        
        neis_go_menu(page, '학급담임', '성적', '학생평가', '학기말종합의견')
        messagebox.showinfo("완료", "학기말 종합의견(담임) 메뉴로 이동했습니다.")
    except Exception as e:
        _handle_error(e)

def neis_class_hakjjong():
    """학기말 종합의견(교과) 메뉴로 이동"""
    try:
        # 업무포털 먼저 접속하여 기존 창 확보
        open_eduptl()
        
        # 현재 업무포털 페이지에서 나이스 URL로 이동
        page = browser_manager.get_page()
        page.goto(urls['나이스'])
             
        neis_go_menu(page, '교과담임', '성적', '학생평가', '학기말종합의견')
        messagebox.showinfo("완료", "학기말 종합의견(교과) 메뉴로 이동했습니다.")
    except Exception as e:
        _handle_error(e)