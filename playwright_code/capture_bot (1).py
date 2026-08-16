from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime

# config에서 타겟 URL과 제외 리스트를 불러옴
from config import TARGET_URLS, EXCLUDE_DOMAINS

# 쿠키 배너 클릭 + 상품명/제조원/규격 추출 로직은 product_extractor.py에 공통화됨
from product_extractor import dismiss_cookie_banner, extract_product_fields, save_extracted_data

# ============================================================
# 메인 캡처 봇
# ============================================================
def run_capture_bot():
    """제외 도메인을 필터링하고, 쿠키 배너를 자동으로 닫은 뒤,
    output 폴더에 전체화면 캡처 + 상품명/제조원/규격 데이터를 저장하는 봇"""

    # 1. 봇 차단 도메인(네이버, 쿠팡 등)을 걸러내는 필터링 로직
    valid_urls = []
    print("🔍 URL 필터링 검사 중...")
    for url in TARGET_URLS:
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

    all_results = []

    with sync_playwright() as p:
        print("\n🌐 Chrome 실행 중...")

        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--window-position=0,0", "--start-maximized"]
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        try:
            for idx, url in enumerate(valid_urls, 1):
                safe_name = url.replace("https://", "").replace("http://", "").split("/")[0].replace(".", "_")

                print(f"\n[{idx}/{len(valid_urls)}] 🌐 [{safe_name}] 접속 및 캡처 중...")

                # 1. 페이지 이동
                page.goto(url, wait_until='load', timeout=30000)
                print("   ⏳ 뼈대 로딩 완료...")
                time.sleep(2)

                # 2. 🍪 쿠키/팝업 배너 자동 클릭으로 닫기 (숨기지 않고 실제 클릭!)
                dismiss_cookie_banner(page)

                # 혹시 남아있는 팝업/오버레이는 안전하게 추가로 숨김 처리 (보조 수단)
                try:
                    page.evaluate("""
                        document.querySelectorAll('[class*="cookie"], [id*="cookie"], [class*="popup"], [id*="popup"]').forEach(el => {
                            el.style.display = 'none';
                        });
                    """)
                except Exception:
                    pass

                time.sleep(1)

                # 3. 🐢 찔끔찔끔 스크롤 작전 (지연 로딩 데이터 깨우기)
                print("   ⏬ 스크롤 내리며 데이터 깨우는 중...")
                for i in range(1, 5):
                    page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * ({i}/4))')
                    time.sleep(2)

                # 4. 맨 위로 원상복구
                page.evaluate('window.scrollTo(0, 0)')
                time.sleep(1)

                # 5. 📋 상품명 / 제조원 / 규격 추출
                print("   🔎 상품명/제조원/규격 추출 중...")
                fields = extract_product_fields(page)
                print(f"      - 상품명: {fields['상품명'] or '(못 찾음)'}")
                print(f"      - 제조원: {fields['제조원'] or '(못 찾음)'}")
                print(f"      - 규격:  {fields['규격'] or '(못 찾음)'}")

                # 6. 전체화면 캡처
                screenshot_name = f"{idx}_{safe_name}_full_page.png"
                full_path = os.path.join(session_output_dir, screenshot_name)
                page.screenshot(path=full_path, full_page=True)
                print(f"   ✅ 전체화면 캡처 완료 및 저장: {full_path}")

                all_results.append({
                    "url": url,
                    "상품명": fields["상품명"],
                    "제조원": fields["제조원"],
                    "규격": fields["규격"],
                    "screenshot": screenshot_name,
                })

            print(f"\n🎉 모든 유효 페이지 캡처 완료!")
            print(f"📂 저장 위치: {os.path.abspath(session_output_dir)}")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            error_path = os.path.join(session_output_dir, "error_screenshot.png")
            page.screenshot(path=error_path)

        finally:
            save_extracted_data(session_output_dir, all_results)
            print("\n⏸️  5초 후 브라우저가 닫힙니다...")
            time.sleep(5)
            browser.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 URL 필터링 오토 캡처 봇 실행 (쿠키 자동클릭 + 데이터 추출)")
    print("=" * 60)
    run_capture_bot()
