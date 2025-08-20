# utils.py (수정된 코드)

import os.path
import configparser
from tkinter import filedialog, messagebox
import pandas as pd
from playwright.sync_api import Page, Browser, expect

# (urls 딕셔너리 등 다른 부분은 변경 없음)
urls = {
    '업무포털 메인': 'https://jbe.eduptl.kr/bpm_man_mn00_001.do',
    '업무포털 로그인': 'https://jbe.eduptl.kr/bpm_lgn_lg00_001.do',
    '에듀파인': 'http://klef.jbe.go.kr/',
    '나이스': 'https://jbe.neis.go.kr/cmc_fcm_lg01_000.do?data=W2U5NE1jNlpoNGdUR2tKaFJyWFp4TGE3SGpURFViRWNYVHBWR1Q2ZTdUaHVhQVpjWDd2QnpibnFwYmNIMkljZTI5VTMxUjgvZHdyYTMyOEE0d0xnZllzQ2RDTmhvYzdDVGlJdDd2KzRMbzU1ckNNL05RZkVVVjRzcWJrWENGK2xFeVZ2a3c3OWw1TUlTemcxcGoxczNVanhTNitGT1JwUTZ1d3l6SjAzUDVyST0='
}

def login(page: Page):
    """업무포털에서 로그인하는 함수 (Playwright)"""
    # 1. 전자인증서 로그인 버튼 클릭
    page.locator('button.elec-log-btn').click()
    
    # 2. 새 창이 열릴 때까지 대기
    page.wait_for_timeout(2000)
    
    # 3. 비밀번호 입력 필드에 비밀번호 입력
    password_input = page.locator('input[name="certPassword"]')
    password = get_password_from_file()
    password_input.fill(password)
    
    # 4. kc-btn-blue 클래스 버튼 클릭 (확인 버튼)
    page.locator('button.kc-btn-blue').click()
    
    # --- [수정된 부분] ---
    # 여기서 대기하지 않고, 함수를 호출한 쪽에서 대기하도록 책임을 넘깁니다.
    # page.wait_for_load_state('networkidle') # 이 줄을 삭제 또는 주석 처리합니다.



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