#!/usr/bin/env python3
"""Check persistent categories, crop evidence, selected strokes and borderless range."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from playwright.sync_api import sync_playwright
from build_report import build, FIGMA_ICON

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'assets/example-manifest.json').read_text())
# Supplied image fixture tests the actual embedded image path, independently of missing-evidence UI.
manifest['pages'][1]['images'].update(actual=FIGMA_ICON, design=FIGMA_ICON)
with TemporaryDirectory() as directory, sync_playwright() as p:
    report = Path(directory) / 'report.html'
    report.write_text(build(manifest))
    browser = p.chromium.launch()
    try:
        page = browser.new_page(viewport={'width':1317,'height':936}, reduced_motion='reduce')
        page.goto(report.as_uri())
        for unit in manifest['pages']:
            page.evaluate('(id)=>showPage(id)',unit['id'])
            view = page.locator('.acceptance-view:visible')
            headings = view.locator('.issue-group > summary').all_text_contents()
            assert [x.split('（')[0] for x in headings[:4]] == ['字号问题','颜色问题','间距问题','元素尺寸问题']
            for count in view.locator('.zero-count').all():
                assert count.evaluate('e=>getComputedStyle(e).color') == 'rgb(19, 179, 107)'
            for card in view.locator('.issue').all():
                assert card.locator('.issue-preview figure').count() == 2
            view.locator('.issue-group').last.locator('summary').click()
            if unit['id'] == 'h5-example-page':
                assert view.locator('.issue-preview-image image').count() == 2
                assert view.locator('.issue-preview-missing').count() == 0
            else:
                assert view.locator('.issue-preview-missing').count() == 4
            view.locator('.issue').first.click()
            actual = view.locator('.side-by-side .problem.is-highlighted').first
            expected = view.locator('.side-by-side .issue-mark.is-selected .expected').first
            assert actual.evaluate('e=>getComputedStyle(e).strokeWidth') == expected.evaluate('e=>getComputedStyle(e).strokeWidth') == '2px'
            view.locator('[data-compare=overlay]').click()
            slider = view.locator('input[type=range]')
            assert slider.evaluate('e=>getComputedStyle(e).borderTopWidth') == '0px'
            slider.fill('70')
            assert view.locator('.actual-composite').evaluate('e=>getComputedStyle(e).opacity') == '0.7'
        page.screenshot(path='/tmp/issue-presentation.png',full_page=True)
    finally:
        browser.close()
print('Issue presentation checks passed.')
