import json
import os
import re
import time
from datetime import datetime
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from config import (
    BASE_DIR,
    BROWSER_PROFILE_DIR,
    EXCLUDE_DOMAINS,
    HEADLESS,
    MANUAL_CHALLENGE_WAIT_SECONDS,
    PRODUCT_REGION_SELECTORS,
    TARGET_URLS,
    WARMUP_URLS,
)


DEFAULT_VIEWPORT = {"width": 1500, "height": 1000}
BLOCKED_PATTERN = re.compile(
    r"access\s*denied|request\s*blocked|unusual\s*traffic|automated\s*(request|access)|"
    r"just\s*a\s*moment|checking\s*your\s*browser|cloudflare|"
    r"비정상적인?\s*접근|접근이?\s*(제한|차단)|봇\s*(확인|검토)|검토\s*번호",
    re.IGNORECASE,
)
MORE_PATTERN = re.compile(
    r"상세\s*(정보|설명)\s*더\s*보기|상품\s*정보\s*더\s*보기|전체\s*보기|더보기|"
    r"view\s*more|show\s*more|more\s*details?",
    re.IGNORECASE,
)


def safe_name(url):
    host = urlparse(url).hostname or "unknown"
    return host.replace(".", "_")


def is_blocked(page):
    try:
        sample = f"{page.title()} {page.locator('body').inner_text(timeout=3000)[:1500]}"
        return bool(BLOCKED_PATTERN.search(sample))
    except Exception:
        return False


def warm_up(page, url):
    host = urlparse(url).hostname or ""
    warmup = WARMUP_URLS.get(host)
    if not warmup:
        return
    print(f"   워밍업 방문: {warmup}")
    try:
        page.goto(warmup, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2000)
    except Exception as error:
        print(f"   워밍업 실패(상세 페이지는 계속 진행): {error}")


def wait_for_manual_challenge(page):
    """표시 브라우저에서 사용자가 사이트의 정상 확인 절차를 마칠 시간을 준다."""
    if HEADLESS or not is_blocked(page):
        return not is_blocked(page)

    print("   보안 확인 화면입니다. 열린 Chrome에서 정상 확인 절차를 완료하세요.")
    deadline = time.time() + MANUAL_CHALLENGE_WAIT_SECONDS
    while time.time() < deadline:
        page.wait_for_timeout(2000)
        if not is_blocked(page):
            print("   보안 확인 완료. 저장된 브라우저 세션을 다음 실행에도 재사용합니다.")
            return True
    return False


def dismiss_consent(page):
    pattern = re.compile(
        r"accept all|allow all|i agree|got it|모두\s*수락|전체\s*동의|모두\s*동의|동의",
        re.IGNORECASE,
    )
    try:
        candidates = page.get_by_role("button", name=pattern)
        for index in range(min(candidates.count(), 5)):
            button = candidates.nth(index)
            if button.is_visible(timeout=500):
                button.click(timeout=2000)
                page.wait_for_timeout(500)
                return True
    except Exception:
        pass
    return False


def expand_details(page):
    expanded = 0
    try:
        candidates = page.locator("button, [role=button], summary").filter(has_text=MORE_PATTERN)
        for index in range(min(candidates.count(), 8)):
            target = candidates.nth(index)
            try:
                if target.is_visible(timeout=300):
                    target.click(timeout=1500)
                    expanded += 1
                    page.wait_for_timeout(500)
            except Exception:
                continue
    except Exception:
        pass
    return expanded


def wake_lazy_content(page):
    previous_height = 0
    stable = 0
    for _ in range(18):
        try:
            height = page.evaluate("document.documentElement.scrollHeight")
            page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        except Exception:
            break
        page.wait_for_timeout(800)
        if height == previous_height:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
            previous_height = height
    try:
        page.evaluate("window.scrollTo(0, 0)")
    except Exception:
        pass


def extract_tables(page):
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('table')).map((table, tableIndex) => ({
            table_index: tableIndex + 1,
            rows: Array.from(table.querySelectorAll('tr')).map(row =>
                Array.from(row.querySelectorAll('th,td')).map(cell => ({
                    text: cell.innerText.trim(),
                    rowspan: Number(cell.getAttribute('rowspan') || 1),
                    colspan: Number(cell.getAttribute('colspan') || 1)
                }))
            ).filter(row => row.length)
        })).filter(table => table.rows.length)"""
    )


def save_page_sources(page, prefix):
    visible_text = page.locator("body").inner_text(timeout=10000)
    with open(prefix + "_dom.txt", "w", encoding="utf-8") as output:
        output.write(visible_text)

    tables = extract_tables(page)
    with open(prefix + "_tables.json", "w", encoding="utf-8") as output:
        json.dump(tables, output, ensure_ascii=False, indent=2)

    with open(prefix + "_tables.txt", "w", encoding="utf-8") as output:
        for table in tables:
            output.write(f"[표 {table['table_index']}]\n")
            for row in table["rows"]:
                output.write("\t".join(cell["text"] for cell in row) + "\n")
            output.write("\n")
    return len(tables)


def capture_product_region(page, url, prefix):
    """사이트별 상품 본문만 별도 저장해 메뉴·광고가 OCR을 방해하지 않게 한다."""
    host = urlparse(url).hostname or ""
    selectors = PRODUCT_REGION_SELECTORS.get(host, ["main"])
    for selector in selectors:
        try:
            region = page.locator(selector).first
            if not region.is_visible(timeout=800):
                continue
            box = region.bounding_box()
            if not box or box["width"] < 300 or box["height"] < 150:
                continue
            path = prefix + "_product.png"
            region.screenshot(path=path, animations="disabled")
            with open(prefix + "_product_dom.txt", "w", encoding="utf-8") as output:
                output.write(region.inner_text(timeout=5000))
            return path, selector
        except Exception:
            continue
    return None, None


def capture_one(page, url, index, total, output_dir):
    name = safe_name(url)
    prefix = os.path.join(output_dir, f"{index}_{name}")
    print(f"\n[{index}/{total}] 접속: {url}")
    warm_up(page, url)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("load", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    if is_blocked(page) and not wait_for_manual_challenge(page):
        page.screenshot(path=prefix + "_blocked.png", full_page=True)
        metadata = {"url": url, "status": "blocked", "title": page.title()}
        with open(prefix + "_metadata.json", "w", encoding="utf-8") as output:
            json.dump(metadata, output, ensure_ascii=False, indent=2)
        print("   차단 화면이 유지되어 상품 캡처와 OCR 대상에서 제외했습니다.")
        return "blocked"

    if dismiss_consent(page):
        print("   쿠키 동의 창을 닫았습니다.")
    expanded = expand_details(page)
    if expanded:
        print(f"   상세정보 버튼 {expanded}개를 펼쳤습니다.")
    wake_lazy_content(page)
    expand_details(page)

    table_count = save_page_sources(page, prefix)
    product_path, product_selector = capture_product_region(page, url, prefix)
    screenshot_path = prefix + "_full_page.png"
    page.screenshot(path=screenshot_path, full_page=True, animations="disabled")
    metadata = {
        "url": url,
        "status": "captured",
        "title": page.title(),
        "final_url": page.url,
        "table_count": table_count,
        "screenshot": screenshot_path,
        "product_screenshot": product_path,
        "product_selector": product_selector,
    }
    with open(prefix + "_metadata.json", "w", encoding="utf-8") as output:
        json.dump(metadata, output, ensure_ascii=False, indent=2)
    print(f"   캡처 완료: {screenshot_path} / DOM 표 {table_count}개")
    return "captured"


def run_capture_bot():
    urls = [
        url for url in TARGET_URLS
        if not any(excluded.lower() in (urlparse(url).hostname or "").lower() for excluded in EXCLUDE_DOMAINS)
    ]
    output_dir = os.path.join(
        BASE_DIR, "output", "capture_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)
    print(f"캡처 대상 {len(urls)}개 / 저장 위치: {output_dir}")

    results = []
    with sync_playwright() as playwright:
        # 실제 Chrome 프로필과 섞지 않는 전용 영구 프로필이다. 정상 로그인/보안 확인 상태만 재사용한다.
        context = playwright.chromium.launch_persistent_context(
            BROWSER_PROFILE_DIR,
            channel="chrome",
            headless=HEADLESS,
            viewport=DEFAULT_VIEWPORT,
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            args=["--start-maximized"],
        )
        try:
            for index, url in enumerate(urls, 1):
                page = context.new_page()
                try:
                    status = capture_one(page, url, index, len(urls), output_dir)
                except Exception as error:
                    status = "error"
                    print(f"   오류: {error}")
                    try:
                        page.screenshot(
                            path=os.path.join(output_dir, f"{index}_{safe_name(url)}_error.png"),
                            full_page=True,
                        )
                    except Exception:
                        pass
                finally:
                    page.close()
                results.append({"url": url, "status": status})
        finally:
            context.close()

    with open(os.path.join(output_dir, "capture_summary.json"), "w", encoding="utf-8") as output:
        json.dump(results, output, ensure_ascii=False, indent=2)
    print(f"\n완료: {output_dir}")


if __name__ == "__main__":
    run_capture_bot()
