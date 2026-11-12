#!/usr/bin/env python3
"""
verify.py — автопроверка шаблона tutor-platform-template.

Шаги:
  1. generate.py + config.example.json -> временный dist-тест
  2. 0 оставшихся плейсхолдеров {{...}} в результате (и в dist/index.html)
  3. node --check на всех inline <script> блоках
  4. Нет захардкоженного PIN "1234" и "service_role" в template.html и dist/index.html
  5. Playwright (если установлен): 0 pageerror, scrollWidth <= clientWidth
     на 1440x900 и 360x800; картинки отдаются из ../maria-math/assets через
     временный локальный сервер (структура dist не меняется), RPC Supabase
     замокан — база не затрагивается.

Exit code 0 = все проверки пройдены.
"""

import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(ROOT, "template.html")
DIST_INDEX = os.path.join(ROOT, "dist", "index.html")
ASSETS_DIR = os.path.join(os.path.dirname(ROOT), "maria-math", "assets")
VIEWPORTS = [(1440, 900), (360, 800)]
TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE)

FAILURES = []


def report(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)


def step_generate(workdir):
    print("[1/5] generate.py + config.example.json -> временный dist-тест")
    out = os.path.join(workdir, "index.html")
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "generate.py"),
         "--config", os.path.join(ROOT, "config.example.json"),
         "--output", out],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        report(False, "generate.py", (proc.stderr or proc.stdout).strip())
        return None
    report(True, "generate.py", out)
    return out


def step_placeholders(generated):
    print("[2/5] Плейсхолдеры {{...}}")
    targets = [("сгенерированный index.html", generated)]
    if os.path.exists(DIST_INDEX):
        targets.append(("dist/index.html", DIST_INDEX))
    for label, path in targets:
        if not path or not os.path.exists(path):
            report(False, f"placeholders: {label}", "файл отсутствует")
            continue
        with open(path, encoding="utf-8") as f:
            leftover = TOKEN_RE.findall(f.read())
        report(not leftover, f"placeholders: {label}",
               f"{len(leftover)} шт." + (f" {sorted(set(leftover))[:5]}" if leftover else ""))


def step_node_check(generated):
    print("[3/5] node --check на inline <script> блоках")
    node = shutil.which("node")
    if not node:
        report(False, "node --check", "node не найден в PATH")
        return
    with open(generated, encoding="utf-8") as f:
        html = f.read()
    blocks = SCRIPT_RE.findall(html)
    if not blocks:
        report(False, "node --check", "inline <script> блоки не найдены")
        return
    for i, code in enumerate(blocks, 1):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        try:
            proc = subprocess.run([node, "--check", tmp_path],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")
            report(proc.returncode == 0, f"node --check script #{i} ({len(code)} симв.)",
                   (proc.stderr or "").strip().splitlines()[-1] if proc.returncode else "exit 0")
        finally:
            os.unlink(tmp_path)


def step_forbidden_strings():
    print("[4/5] Запрещённые строки: '1234' (PIN) и 'service_role'")
    for path in (TEMPLATE, DIST_INDEX):
        label = os.path.relpath(path, ROOT)
        if not os.path.exists(path):
            report(False, f"forbidden: {label}", "файл отсутствует")
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        hits = [s for s in ("1234", "service_role") if s in content]
        report(not hits, f"forbidden: {label}", f"найдено: {hits}" if hits else "не найдены")


class _DistHandler(http.server.SimpleHTTPRequestHandler):
    """Раздаёт временный dist, /assets/* берёт из maria-math/assets (dist не меняется)."""

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def translate_path(self, path):
        path = urllib.parse.urlparse(path).path
        if path.startswith("/assets/"):
            rel = urllib.parse.unquote(path[len("/assets/"):])
            return os.path.join(ASSETS_DIR, rel)
        return super().translate_path(path)

    def log_message(self, *args):
        pass


def _mock_rpc(route):
    fn = route.request.url.rsplit("/", 1)[-1]
    body = {"site": {"config": {}}, "slot_entries": [], "reviews": []} if fn == "get_public_site_bundle" else {}
    route.fulfill(status=200, content_type="application/json", body=json.dumps(body))


def step_playwright(generated):
    print("[5/5] Playwright: pageerror + overflow на 1440x900 и 360x800")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [SKIP] Playwright не установлен — браузерные проверки пропущены")
        return

    handler = lambda *a, **kw: _DistHandler(*a, directory=os.path.dirname(generated), **kw)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for width, height in VIEWPORTS:
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                page_errors, failed_assets = [], []
                page.on("pageerror", lambda err: page_errors.append(str(err)))
                page.on("response", lambda r: failed_assets.append(f"{r.status} {r.url}")
                        if r.status >= 400 and f"127.0.0.1:{port}" in r.url else None)
                page.route("**/rest/v1/rpc/*", _mock_rpc)
                page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load", timeout=60000)
                page.wait_for_function("document.body.getAttribute('data-cloud-ready') === 'true'", timeout=30000)
                page.wait_for_timeout(1500)
                overflow = page.evaluate(
                    "document.documentElement.scrollWidth - document.documentElement.clientWidth")
                broken_imgs = page.evaluate(
                    "Array.from(document.images).filter(i => i.src && !i.complete || (i.complete && i.naturalWidth === 0 && i.src.startsWith(location.origin))).length")
                report(not page_errors, f"{width}x{height}: 0 pageerror",
                       "; ".join(page_errors[:3]) if page_errors else "0 JS-ошибок")
                report(overflow <= 0, f"{width}x{height}: scrollWidth <= clientWidth", f"overflow = {overflow}px")
                report(not failed_assets and broken_imgs == 0, f"{width}x{height}: битые пути/картинки",
                       f"http>=400: {failed_assets[:3]}, broken img: {broken_imgs}")
                context.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def main():
    print("=== verify.py: tutor-platform-template ===")
    with tempfile.TemporaryDirectory(prefix="tutor-verify-") as workdir:
        generated = step_generate(workdir)
        if generated:
            step_placeholders(generated)
            step_node_check(generated)
        step_forbidden_strings()
        if generated:
            step_playwright(generated)
    print()
    if FAILURES:
        print(f"ИТОГ: FAIL ({len(FAILURES)}): {FAILURES}")
        return 1
    print("ИТОГ: PASS — все проверки пройдены")
    return 0


if __name__ == "__main__":
    sys.exit(main())