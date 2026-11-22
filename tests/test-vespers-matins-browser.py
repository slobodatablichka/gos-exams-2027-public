#!/usr/bin/env python3
"""Browser acceptance: original table layout, all three digital views and mobile widths."""
import contextlib
import functools
import http.server
import json
import pathlib
import re
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "assets/liturgics/vespers-matins-data.json").read_text(encoding="utf-8"))
SOURCE = (ROOT / "subjects/liturgics/2027/vespers-matins.md").read_text(encoding="utf-8")
ASSET_REF = "{{ '/assets/liturgics/vespers-matins-data.json' | relative_url }}"
ICON_REF = "{{ '/assets/liturgics/service-signs/' | relative_url }}"

assert ASSET_REF in SOURCE and ICON_REF in SOURCE
style = re.search(r"<style>[\s\S]*?</style>", SOURCE)
assert style, "Missing published table stylesheet"
start = SOURCE.index('<div class="vm-tool"')
end = SOURCE.index("<script src=", start)
fragment = SOURCE[start:end]
fragment = fragment.replace(ASSET_REF, "/assets/liturgics/vespers-matins-data.json")
fragment = fragment.replace(ICON_REF, "/assets/liturgics/service-signs/")
page_html = ('<!doctype html><html lang="ru"><head><meta charset="UTF-8">'
             '<meta name="viewport" content="width=device-width, initial-scale=1">'
             + style.group() + '</head><body>' + fragment +
             '<script defer src="/assets/liturgics/vespers-matins-digital.js"></script>'
             '</body></html>')

with tempfile.TemporaryDirectory() as directory:
    tmp = pathlib.Path(directory)
    (tmp / "index.html").write_text(page_html, encoding="utf-8")
    (tmp / "assets").symlink_to(ROOT / "assets", target_is_directory=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"
    try:
        with sync_playwright() as playwright:
            chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
            launch_args = {"headless": True, "args": ["--no-sandbox"]}
            if chrome:
                launch_args["executable_path"] = chrome
            browser = playwright.chromium.launch(**launch_args)
            try:
                for width,height in [(1440,900),(390,844),(320,700)]:
                    pg = browser.new_page(viewport={"width":width,"height":height}, device_scale_factor=1)
                    errors = []
                    pg.on("pageerror", lambda e: errors.append(str(e)))
                    pg.goto(url, wait_until="networkidle")
                    pg.wait_for_function("document.querySelectorAll('#vm-service option').length === 17", timeout=15000)
                    assert not errors, errors
                    assert pg.locator("#vm-status").inner_text().strip() == ""
                    assert pg.locator("#vm-table thead tr").count() == 2
                    assert pg.locator("#vm-table tbody tr").count() == 29, "All 29 original physical bands must be visible"
                    assert pg.locator("#vm-table thead .vm-group").count() == 9
                    assert pg.locator("#vm-row option").count() == 23
                    merged = pg.locator("#vm-table tbody td[colspan], #vm-table tbody td[rowspan], #vm-table tbody th[colspan], #vm-table tbody th[rowspan]").count()
                    assert merged == len(DATA["source_layout"]["merged_regions"]), (width, merged, len(DATA["source_layout"]["merged_regions"]))
                    assert pg.locator("#vm-table tbody tr").first.inner_text().find("Господи") >= 0
                    imgs = pg.locator("#vm-table thead .vm-icon")
                    assert imgs.count() >= 7
                    assert all(imgs.nth(i).evaluate("(img) => img.complete && img.naturalWidth > 0") for i in range(imgs.count()))
                    pg.locator('[data-vm-view="service"]').click()
                    pg.locator("#vm-service").select_option("c17")
                    assert pg.locator("#vm-one").is_visible()
                    assert pg.locator("#vm-one .vm-card").count() == 24
                    assert "воскр. и праздн." in pg.locator("#vm-one").inner_text()
                    pg.locator('[data-vm-view="compare"]').click()
                    pg.locator("#vm-row").select_option("r23")
                    assert pg.locator("#vm-compare .vm-card").count() == 17
                    assert "← →" in pg.locator("#vm-compare").inner_text()
                    pg.locator('[data-vm-view="full"]').click()
                    assert pg.locator("#vm-full").is_visible()
                    assert pg.locator("#vm-table tbody tr").count() == 29
                    print(f"PASS: {width}px, 29 bands, {merged} merged regions, 17 variants, all three modes", flush=True)
                    pg.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
