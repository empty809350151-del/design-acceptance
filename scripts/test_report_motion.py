#!/usr/bin/env python3
"""Exercise disclosure and tab transitions, including interrupted animations."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from playwright.sync_api import sync_playwright
from build_report import build


def check_motion():
    root = Path(__file__).resolve().parents[1]
    with TemporaryDirectory() as directory, sync_playwright() as p:
        output = Path(directory) / 'report.html'
        output.write_text(build(json.loads((root / 'assets/example-manifest.json').read_text())))
        browser = p.chromium.launch()
        try:
            for reduced in ('no-preference', 'reduce'):
                page = browser.new_page(viewport={'width': 1317, 'height': 936}, reduced_motion=reduced)
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(output.as_uri())
                page.evaluate('document.getAnimations().forEach(a=>a.finish())')
                detail = page.locator('.acceptance-view:visible .issue-group').first
                summary = detail.locator('summary')
                summary.focus()
                page.keyboard.press('Enter')
                if reduced == 'no-preference':
                    assert detail.evaluate('e=>e.getAnimations().length') > 0
                page.wait_for_function("!document.querySelector('.acceptance-view:not([hidden]) .issue-group').open")
                # Open then reverse twice before finishing: last requested state wins.
                summary.evaluate('e=>{e.click();e.click();e.click()}')
                page.wait_for_function("document.querySelector('.acceptance-view:not([hidden]) .issue-group').open && !document.querySelector('.acceptance-view:not([hidden]) .issue-group').dataset.expanding")
                assert detail.evaluate("e=>e.style.overflow==='' && e.style.height===''")
                page.locator('.acceptance-view:visible [data-compare=overlay]').click()
                if reduced == 'no-preference':
                    assert page.locator('.acceptance-view:visible .overlay-panel').evaluate('e=>e.getAnimations().length') > 0
                page.evaluate("showPage('h5-example-page');showPage('example-page');showPage('h5-example-page')")
                page.evaluate('document.getAnimations().forEach(a=>a.finish())')
                assert page.locator('.acceptance-view:visible').get_attribute('data-page') == 'h5-example-page'
                assert page.locator('.acceptance-view:visible .side-by-side').is_visible()
                panel = page.locator('.acceptance-view:visible .controls').bounding_box()
                assert abs(panel['y']) < 1 and abs(panel['x'] + panel['width'] - 1317) < 1
                toggle = page.locator('.sidebar-toggle')
                toggle.click()
                assert toggle.get_attribute('aria-expanded') == 'false'
                toggle.click()
                assert toggle.get_attribute('aria-expanded') == 'true'
                page.evaluate('document.getAnimations().forEach(a=>a.finish())')
                if reduced == 'reduce':
                    assert page.evaluate('document.getAnimations().length') == 0
                assert not errors, errors
                page.close()
        finally:
            browser.close()
    print('Motion checks passed: keyboard, rapid reversal, tabs, sidebar, reduced motion.')


if __name__ == '__main__':
    check_motion()
