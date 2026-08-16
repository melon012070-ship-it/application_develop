from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime

# config에서 타겟 URL과 제외 리스트를 불러옴
from config import TARGET_URLS, EXCLUDE_DOMAINS

def run_capture_bot():
    """제외 도메인을 필터링하고 output 폴더에 전체화면을 캡처하는 봇"""

    # 1. 봇 차단 도메인(네이버, 쿠팡 등)을 걸러내는 필터링 로직
    valid_urls = []
    print("🔍 URL 필터링 검사 중...")
    for url in TARGET_URLS:
        # URL에 제외 키워드가 포함되어 있는지 확인
        is_excluded = any(domain in url for domain in EXCLUDE_DOMAINS)
        if is_excluded:
            print(f"   🚫 제외됨 (블랙리스트 매칭): {url}")
        else:
            valid_urls.append(url)
            print(f"   ✅ 캡처 대상 승인: {url}")

    if not valid_urls:
        print("\n❌ 캡처할 수 있는 유효한 URL이 없습니다!")
        return

    # 2. output/ 폴더 내부에 타임스탬프 세션 폴더 생성
    base_output_dir = 'output'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_output_dir = os.path.join(base_output_dir, f'capture_{timestamp}')
    os.makedirs(session_output_dir, exist_ok=True)

    print(f"\n📁 최종 저장 폴더: {session_output_dir}")
    print("=" * 60)

    with sync_playwright() as p:
        print("\n🌐 Chrome 실행 중...")

        browser = p.chromium.launch(
            headless=False,  
            channel="chrome",
            args=["--window-position=0,0", "--start-maximized"] # 1번 모니터 왼쪽 위 고정 및 최대화
        )
        # 창이 최대화되었으니 고정 뷰포트 대신 꽉 찬 화면(no_viewport) 사용
        context = browser.new_context(no_viewport=True) 
        page = context.new_page()

        try:
            for idx, url in enumerate(valid_urls, 1):
                # URL에서 파일명으로 쓸 만한 안전한 이름 추출 (예: python_org)
                safe_name = url.replace("https://", "").replace("http://", "").split("/")[0].replace(".", "_")
                
                print(f"\n[{idx}/{len(valid_urls)}] 🌐 [{safe_name}] 접속 및 캡처 중...")

                # 1. 페이지 이동 (load 옵션으로 무한 로딩 방지)
                page.goto(url, wait_until='load', timeout=30000)
                print("   ⏳ 뼈대 로딩 완료, 동적 데이터(표) 대기 중...")
                time.sleep(3)

                # 2. 🔫 팝업 & 쿠키 배너 암살 (JS 주사)
                try:
                    page.evaluate("""
                        document.querySelectorAll('[class*="cookie"], [id*="cookie"], [class*="popup"], [id*="popup"]').forEach(el => {
                            el.style.display = 'none';
                        });
                    """)
                    print("   🧹 쿠키 및 팝업 배너 청소 완료!")
                except Exception as e:
                    pass # 실패해도 무시하고 진행

                # 3. 🐢 찔끔찔끔 스크롤 작전 (미스미 같은 지연 로딩 데이터 깨우기)
                print("   ⏬ 스크롤 내리며 데이터 깨우는 중...")
                for i in range(1, 5): # 4번에 걸쳐서 화면을 내림
                    page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * ({i}/4))')
                    time.sleep(2) # 각 구간마다 리스트(표)가 뜰 시간 2초씩 주기

                # 4. 맨 위로 원상복구 및 최종 전체화면 캡처 (부분 캡처 삭제!)
                page.evaluate('window.scrollTo(0, 0)')
                time.sleep(1)
                
                full_path = os.path.join(session_output_dir, f"{idx}_{safe_name}_full_page.png")
                page.screenshot(path=full_path, full_page=True)
                print(f"   ✅ 전체화면 캡처 완료 및 저장: {full_path}")

            print("\n🎉 모든 유효 페이지 캡처 완료!")
            print(f"📂 저장 위치: {os.path.abspath(session_output_dir)}")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            error_path = os.path.join(session_output_dir, "error_screenshot.png")
            page.screenshot(path=error_path)

        finally:
            print("\n⏸️  5초 후 브라우저가 닫힙니다...")
            time.sleep(5)
            browser.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 URL 필터링 오토 캡처 봇 실행")
    print("=" * 60)
    run_capture_bot()