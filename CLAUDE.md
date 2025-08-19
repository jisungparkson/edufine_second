# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Korean educational portal automation tool that uses Playwright for web automation and Tkinter for the GUI interface. The application automates tasks in the Korean education systems: 업무포털 (Work Portal) and 나이스 (NEIS).

## Setup and Dependencies

**Installation:**
```bash
pip install -r requirements.txt
```

**Browser Setup:**
Before running the application, start Edge in debug mode using:
```bash
start_edge_debug.bat
```
This launches Edge with remote debugging on port 9222, allowing the application to connect to existing browser sessions.

**Required External Files:**
- Password file at `C:\GPKI\password.txt` containing the certificate password
- Excel files for bulk data input (선택된 through file dialog)

## Running the Application

**Start the GUI:**
```bash
python interface.py
```

## Architecture

**Core Components:**

1. **interface.py** - Main Tkinter GUI with buttons for different automation tasks
2. **btn_commands.py** - Contains all automation logic using Playwright
3. **utils.py** - Shared utilities for web navigation, Excel processing, and authentication

**Key Architecture Pattern:**

The application uses a singleton `BrowserManager` class that maintains persistent browser state across operations. This allows:
- Reusing existing browser sessions
- Automatic reconnection to Edge debug instance
- Graceful fallback to new browser instances

**Browser Connection Flow:**
1. Try to connect to existing Edge debug session (port 9222)
2. Look for existing portal tabs to reuse
3. Fall back to launching new browser if connection fails
4. Create new pages/contexts as needed

**Web Automation Pattern:**
All automation functions follow this pattern:
1. Get page via `browser_manager.get_page()`
2. Navigate to portal (calls `open_eduptl()` first)
3. Navigate to NEIS system
4. Use utility functions for menu navigation and data input
5. Handle errors through `_handle_error()` which closes browser resources

**Excel Integration:**
The application processes Excel files with student data:
- Uses pandas for Excel reading
- Expects '번호' (number) column as index
- Supports bulk input of student behavior comments and evaluations

## Key URLs and Systems

- 업무포털 (Work Portal): `https://jbe.eduptl.kr/`
- 나이스 (NEIS): `https://jbe.neis.go.kr/` 
- 에듀파인 (EduFine): `http://klef.jbe.go.kr/`

## Navigation Utilities

**NEIS Menu Navigation:**
Uses 4-level menu structure: `neis_go_menu(page, level1, level2, level3, level4)`

**Common Navigation Patterns:**
- 학급담임 → 학적 → 출결관리 → 출결관리
- 학급담임 → 학생생활 → 행동특성및종합의견 → 행동특성및종합의견  
- 학급담임 → 성적 → 학생평가 → 학기말종합의견
- 교과담임 → 성적 → 학생평가 → 학기말종합의견

## Error Handling

All automation functions use try-catch with `_handle_error()` which:
- Shows error message box to user
- Safely closes all browser resources via `browser_manager.close()`
- Resets manager state for clean restart