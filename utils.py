# utils.py (수정된 코드)

import os.path
import configparser
from tkinter import filedialog, messagebox
import pandas as pd
from playwright.sync_api import Page, Browser, expect, TimeoutError

# (urls 딕셔너리 등 다른 부분은 변경 없음)
urls = {
    '업무포털 메인': 'https://jbe.eduptl.kr/bpm_man_mn00_001.do',
    '업무포털 로그인': 'https://jbe.eduptl.kr/bpm_lgn_lg00_001.do',
    '에듀파인': 'http://klef.jbe.go.kr/',
    '나이스': 'https://jbe.neis.go.kr/cmc_fcm_lg01_000.do?data=W2U5NE1jNlpoNGdUR2tKaFJyWFp4TGE3SGpURFViRWNYVHBWR1Q2ZTdUaHVhQVpjWDd2QnpibnFwYmNIMkljZTI5VTMxUjgvZHdyYTMyOEE0d0xnZllzQ2RDTmhvYzdDVGlJdDd2KzRMbzU1ckNNL05RZkVVVjRzcWJrWENGK2xFeVZ2a3c3OWw1TUlTemcxcGoxczNVanhTNitGT1JwUTZ1d3l6SjAzUDVyST0='
}

def login(page: Page):
    """업무포털에서 로그인하는 함수 (Playwright) - 안정성 강화 버전"""
    try:
        print("전자인증서 로그인 버튼을 찾습니다...")
        login_button = page.locator('button.elec-log-btn')
        expect(login_button).to_be_visible(timeout=10000)
        expect(login_button).to_be_enabled(timeout=10000)
        print("버튼을 클릭합니다.")
        login_button.click()

        page.wait_for_timeout(2000)
        
        print("비밀번호 입력창을 찾습니다...")
        password_input = page.locator('input[name="certPassword"]')
        expect(password_input).to_be_visible(timeout=10000)
        
        password = get_password_from_file()
        password_input.fill(password)
        
        print("여러 개의 '확인' 버튼 중 정확한 버튼을 찾아 클릭합니다...")
        
        # 역할이 'button'이고 이름이 '확인'인 요소를 찾습니다.
        # 이것이 'button.kc-btn-blue'보다 훨씬 더 안정적입니다.
        confirm_button_locator = page.get_by_role("button", name="확인", exact=True)
        
        # 여러 개가 발견되었으므로, 그중 마지막 버튼을 선택합니다.
        # 인증서 창의 메인 확인 버튼은 보통 가장 마지막에 있는 경우가 많습니다.
        final_confirm_button = confirm_button_locator.last
        
        # 마지막 버튼이 클릭 가능한 상태가 될 때까지 기다린 후 클릭
        expect(final_confirm_button).to_be_enabled(timeout=10000)
        final_confirm_button.click()
        print("확인 버튼 클릭 완료")
        
    except TimeoutError as e:
        error_msg = f"로그인 과정에서 요소를 찾을 수 없습니다: {str(e)}"
        print(error_msg)
        messagebox.showerror("로그인 오류", error_msg)
        raise
    except Exception as e:
        error_msg = f"로그인 중 예상치 못한 오류 발생: {str(e)}"
        print(error_msg)
        messagebox.showerror("로그인 오류", error_msg)
        raise



# (이하 다른 모든 함수들은 변경 없음)
# ... (get_password_from_file, neis_go_menu 등)
def get_password_from_file():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    try:
        password_filepath = config['Paths']['password_file']
    except (KeyError, configparser.NoSectionError):
        password_filepath = 'C:\\GPKI\\password.txt'  # 기본값
    
    if not os.path.exists(password_filepath):
        raise FileNotFoundError(f"비밀번호 파일을 찾을 수 없습니다.\n{password_filepath} 경로에 비밀번호를 저장하세요.")
    
    with open(password_filepath, 'r') as file:
        return file.read().strip()
    

# (이하 다른 모든 함수들은 변경 없음)
def neis_go_menu(page: Page, level1: str, level2: str, level3: str, level4: str):
    page.locator(f'ul.cl-navigationbar-bar > li:has-text("{level1}")').click()
    menu_container = page.locator('ul.cl-navigationbar-list.gnb')
    menu_container.locator(f'li.cl-navigationbar-category:has-text("{level2}")').locator(f'li:has-text("{level3}")').click()
    fourth_menu_item = page.locator(f'a.cl-leaf.cl-level-2.cl-sidenavigation-item[title="{level4}"]')
    expect(fourth_menu_item).to_be_visible(timeout=10000)
    fourth_menu_item.click()
    page.wait_for_load_state('networkidle')

def switch_tab(browser: Browser, title_keyword: str) -> Page:
    for page in browser.contexts[0].pages:
        if title_keyword in page.title():
            page.bring_to_front()
            return page
    return None

def open_url_in_new_tab(browser: Browser, url: str) -> Page:
    new_page = browser.new_page()
    new_page.goto(url)
    return new_page

def neis_click_btn(page: Page, button_name: str):
    button_locator = page.get_by_role("button", name=button_name, exact=True)
    expect(button_locator).to_be_visible(timeout=10000)
    button_locator.click()

def get_excel_data() -> pd.DataFrame:
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=(("Excel files", "*.xlsx *.xls"), ("All files", "*.*"))
    )
    if not file_path:
        return None
    return pd.read_excel(file_path, index_col='번호')

def neis_fill_row(page: Page, done: set, data: pd.DataFrame, column: str, student_id_css: str) -> set:
    try:
        selected_row = page.locator('div.cl-grid-row.cl-selected')
        student_id_text = selected_row.locator(student_id_css).inner_text()
        student_id = int(student_id_text)
        textarea = selected_row.locator('textarea.cl-text')
        if student_id in done:
            textarea.press('Tab')
            return done
        if textarea.input_value():
            textarea.press('End')
            textarea.press(' ')
        textarea.press_sequentially(str(data.loc[student_id, column]), delay=10)
        done.add(student_id)
        textarea.press('Tab')
        page.wait_for_timeout(500)
    except Exception as e:
        print(f'데이터 입력 중 오류 발생: {e}')
    finally:
        return done