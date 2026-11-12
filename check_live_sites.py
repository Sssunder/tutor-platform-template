#!/usr/bin/env python3
"""
check_live_sites.py — одним запуском проверяет 3 живых сайта из HANDOFF.md.

Для каждого URL:
  - HTTP 200
  - маркеры Constructor v3: #cfgDefaultTheme, #cfgReviewsChannelUrl, #admReviewLivePreview
  - 0 ошибок консоли (console.error / pageerror) и 0 сетевых ошибок (failed / HTTP >= 400)
  - 0px горизонтального переполнения (scrollWidth <= clientWidth) на 1440x900 и 360x800

Только чтение: страница делает штатные read-only RPC Supabase, ничего не пишется в БД.
Exit code 0 = все сайты прошли все проверки.
"""

import sys
import time

SITES = [
    ("natalia-math", "https://sssunder.github.io/natalia-math/"),
    ("maria-math", "https://sssunder.github.io/maria-math/"),
    ("elen-beauty", "https://sssunder.github.io/elen-beauty/"),
]
MARKERS = ["#cfgDefaultTheme", "#cfgReviewsChannelUrl", "#admReviewLivePreview"]
VIEWPORTS = [(1440, 900), (360, 800)]


def check_site(browser, name, url):
    print(f"\n--- {name}: {url} ---")
    failures = []

    def report(ok, label, detail=""):
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(label)

    for width, height in VIEWPORTS:
        context = browser.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        console_errors, page_errors, net_errors, bundle_seen = [], [], [], []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("requestfailed", lambda r: net_errors.append(f"failed {r.url} ({r.failure})"))
        page.on("response", lambda r: net_errors.append(f"HTTP {r.status} {r.url}") if r.status >= 400 else None)
        page.on("response", lambda r: bundle_seen.append(r.url) if "/rest/v1/rpc/get_public_site_bundle" in r.url else None)

        tag = f"{width}x{height}"
        try:
            resp = page.goto(url, wait_until="load", timeout=60000)
            status = resp.status if resp else 0
            report(status == 200, f"{tag}: HTTP 200", f"status = {status}")
            # Готовность: data-cloud-ready (шаблон/maria) либо завершённый bundle RPC (natalia/elen).
            deadline = time.time() + 20
            while time.time() < deadline:
                ready = page.evaluate("document.body.getAttribute('data-cloud-ready') === 'true'")
                if ready or bundle_seen:
                    break
                page.wait_for_timeout(250)
            page.wait_for_timeout(2000)

            missing = page.evaluate(
                "selectors => selectors.filter(s => !document.querySelector(s))", MARKERS)
            report(not missing, f"{tag}: маркеры Constructor v3",
                   f"отсутствуют: {missing}" if missing else "все 3 на месте")

            overflow = page.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth")
            report(overflow <= 0, f"{tag}: горизонтальное переполнение", f"overflow = {overflow}px")

            errors = console_errors + page_errors + net_errors
            report(not errors, f"{tag}: 0 ошибок консоли/сети",
                   f"{len(errors)} шт.: {errors[:3]}" if errors
                   else "console=0, pageerror=0, network=0")
        except Exception as e:
            report(False, f"{tag}: загрузка/ожидание", str(e).splitlines()[0])
        finally:
            context.close()
    return failures


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("FAIL: Playwright не установлен (pip install playwright && playwright install chromium)")
        return 1

    print("=== check_live_sites.py: живые сайты из HANDOFF.md ===")
    all_failures = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, url in SITES:
            fails = check_site(browser, name, url)
            if fails:
                all_failures[name] = fails
        browser.close()

    print("\n=== ИТОГ ===")
    for name, url in SITES:
        print(f"  {name}: {'FAIL — ' + str(all_failures[name]) if name in all_failures else 'PASS'}")
    if all_failures:
        return 1
    print("Все 3 сайта прошли все проверки.")
    return 0


if __name__ == "__main__":
    sys.exit(main())