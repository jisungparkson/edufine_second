# btn_commands.py (다중 인스턴스 아키텍처 버전)

from playwright.sync_api import sync_playwright, TimeoutError, expect
from utils import urls
from tkinter import messagebox


def _handle_error(e):
    """오류 처리 - 단순히 UI에 오류 메시지만 표시"""
    error_message = f"{type(e).__name__}: {e}"
    messagebox.showerror("오류 발생", error_message)


def navigate_to_neis(app_instance):
    """
    나이스 독립 실행형 함수:
    자체 Playwright 인스턴스와 브라우저를 생성하여 완전 독립적으로 실행
    """
    try:
        print("=== 나이스 독립 세션 시작 ===")
        
        with sync_playwright() as playwright:
            print("새로운 Playwright 인스턴스를 시작합니다...")
            
            # 새 브라우저 실행
            browser = playwright.chromium.launch(
                headless=False, 
                channel="msedge"
            )
            print("새 Edge 브라우저를 실행했습니다.")
            
            # 새 페이지 생성
            page = browser.new_page()
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            # 1단계: 나이스 URL로 직접 이동
            print("1단계: 나이스 사이트로 직접 이동합니다...")
            page.goto(urls['나이스'])
            
            # 2단계: 로그인 페이지로 리디렉션 대기
            print("2단계: 로그인 페이지로의 리디렉션을 감지합니다...")
            try:
                page.wait_for_url("**/bpm_lgn_lg00_001.do**", timeout=30000)
                print("✓ 로그인 페이지로 리디렉션되었습니다.")
            except TimeoutError:
                current_url = page.url
                if 'lg00_001.do' in current_url:
                    print("✓ 이미 로그인 페이지에 있습니다.")
                elif 'neis.go.kr' in current_url:
                    print("✓ 이미 나이스에 로그인되어 있습니다.")
                    messagebox.showinfo("완료", "나이스에 성공적으로 접속했습니다!\n\n"
                                                "작업을 마치신 후 '확인'을 눌러 브라우저를 종료하세요.")
                    return
                else:
                    raise Exception(f"예상된 리디렉션이 발생하지 않았습니다. 현재 URL: {current_url}")
            
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # 3단계: 사용자 수동 로그인 안내
            print("3단계: 사용자 수동 로그인 안내...")
            messagebox.showinfo("나이스 로그인 안내", 
                              "나이스 접속을 위해 업무포털 로그인이 필요합니다.\n\n"
                              "브라우저에서 수동으로 로그인을 완료해주세요.\n"
                              "로그인 완료 후 자동으로 나이스 페이지로 이동됩니다.\n\n"
                              "이 창에서 '확인'을 클릭하고 브라우저에서 로그인해주세요.")
            
            # 4단계: 나이스로 복귀 대기
            print("4단계: 로그인 완료 후 나이스로의 복귀를 대기합니다...")
            try:
                page.wait_for_url("**/neis.go.kr/**", timeout=180000)
                print("✓ 나이스 페이지로 성공적으로 복귀했습니다.")
            except TimeoutError:
                current_url = page.url
                if 'neis.go.kr' in current_url:
                    print("✓ 나이스 페이지에 있습니다.")
                elif 'lg00_001.do' in current_url:
                    raise TimeoutError("로그인이 완료되지 않았습니다. 브라우저에서 로그인을 완료해주세요.")
                else:
                    raise TimeoutError(f"예상된 나이스 복귀가 발생하지 않았습니다. 현재 URL: {current_url}")
            
            # 5단계: 최종 확인 및 사용자 작업 완료 대기
            page.wait_for_load_state("networkidle", timeout=30000)
            print("나이스 페이지에 성공적으로 접속했습니다.")
            
            # ★ 핵심: 사용자 작업 완료까지 대기 (브라우저가 닫히지 않도록)
            messagebox.showinfo("나이스 작업 완료 안내", 
                              "나이스에 성공적으로 접속했습니다! 🎉\n\n"
                              "필요한 작업을 모두 마치신 후\n"
                              "이 창에서 '확인'을 눌러 브라우저를 종료하세요.\n\n"
                              "※ 확인을 누르기 전까지 브라우저가 유지됩니다.")
            
            print("사용자가 작업을 완료했습니다. 브라우저를 종료합니다.")
            
    except Exception as e:
        print(f"나이스 접속 중 오류: {e}")
        _handle_error(e)


def navigate_to_edufine(app_instance):
    """
    K-에듀파인 독립 실행형 함수:
    자체 Playwright 인스턴스와 브라우저를 생성하여 완전 독립적으로 실행
    """
    try:
        print("=== K-에듀파인 독립 세션 시작 ===")
        
        with sync_playwright() as playwright:
            print("새로운 Playwright 인스턴스를 시작합니다...")
            
            # 새 브라우저 실행
            browser = playwright.chromium.launch(
                headless=False, 
                channel="msedge"
            )
            print("새 Edge 브라우저를 실행했습니다.")
            
            # 새 페이지 생성
            page = browser.new_page()
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            # 1단계: K-에듀파인 URL로 직접 이동
            print("1단계: K-에듀파인 사이트로 직접 이동합니다...")
            page.goto(urls['에듀파인'])
            
            # 2단계: 로그인 페이지로 리디렉션 대기
            print("2단계: 로그인 페이지로의 리디렉션을 감지합니다...")
            try:
                page.wait_for_url("**/bpm_lgn_lg00_001.do**", timeout=30000)
                print("✓ 로그인 페이지로 리디렉션되었습니다.")
            except TimeoutError:
                current_url = page.url
                if 'lg00_001.do' in current_url:
                    print("✓ 이미 로그인 페이지에 있습니다.")
                elif 'klef.jbe.go.kr' in current_url:
                    print("✓ 이미 K-에듀파인에 로그인되어 있습니다.")
                    messagebox.showinfo("완료", "K-에듀파인에 성공적으로 접속했습니다!\n\n"
                                                "작업을 마치신 후 '확인'을 눌러 브라우저를 종료하세요.")
                    return
                else:
                    raise Exception(f"예상된 리디렉션이 발생하지 않았습니다. 현재 URL: {current_url}")
            
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # 3단계: 사용자 수동 로그인 안내
            print("3단계: 사용자 수동 로그인 안내...")
            messagebox.showinfo("K-에듀파인 로그인 안내", 
                              "K-에듀파인 접속을 위해 업무포털 로그인이 필요합니다.\n\n"
                              "브라우저에서 수동으로 로그인을 완료해주세요.\n"
                              "로그인 완료 후 자동으로 K-에듀파인 페이지로 이동됩니다.\n\n"
                              "이 창에서 '확인'을 클릭하고 브라우저에서 로그인해주세요.")
            
            # 4단계: K-에듀파인으로 복귀 대기
            print("4단계: 로그인 완료 후 K-에듀파인으로의 복귀를 대기합니다...")
            try:
                page.wait_for_url("**/klef.jbe.go.kr/**", timeout=180000)
                print("✓ K-에듀파인 페이지로 성공적으로 복귀했습니다.")
            except TimeoutError:
                current_url = page.url
                if 'klef.jbe.go.kr' in current_url:
                    print("✓ K-에듀파인 페이지에 있습니다.")
                elif 'lg00_001.do' in current_url:
                    raise TimeoutError("로그인이 완료되지 않았습니다. 브라우저에서 로그인을 완료해주세요.")
                else:
                    raise TimeoutError(f"예상된 K-에듀파인 복귀가 발생하지 않았습니다. 현재 URL: {current_url}")
            
            # 5단계: 최종 확인 및 사용자 작업 완료 대기
            page.wait_for_load_state("networkidle", timeout=30000)
            print("K-에듀파인 페이지에 성공적으로 접속했습니다.")
            
            # ★ 핵심: 사용자 작업 완료까지 대기 (브라우저가 닫히지 않도록)
            messagebox.showinfo("K-에듀파인 작업 완료 안내", 
                              "K-에듀파인에 성공적으로 접속했습니다! 🎉\n\n"
                              "필요한 작업을 모두 마치신 후\n"
                              "이 창에서 '확인'을 눌러 브라우저를 종료하세요.\n\n"
                              "※ 확인을 누르기 전까지 브라우저가 유지됩니다.")
            
            print("사용자가 작업을 완료했습니다. 브라우저를 종료합니다.")
            
    except Exception as e:
        print(f"K-에듀파인 접속 중 오류: {e}")
        _handle_error(e)