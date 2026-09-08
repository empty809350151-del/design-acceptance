#!/usr/bin/env python3
"""Browser regression: animated report must not displace the fixed inspector.

Requires Playwright and Chromium. Animations run through the native Web Animations API.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from playwright.sync_api import sync_playwright
from build_report import build

ROOT = Path(__file__).resolve().parents[1]


class ReportLayoutTest(unittest.TestCase):
    def test_inspector_stays_outside_comparison_during_page_animations(self):
        manifest = json.loads((ROOT / 'assets/example-manifest.json').read_text())
        with TemporaryDirectory() as directory, sync_playwright() as playwright:
            report = Path(directory) / 'report.html'
            report.write_text(build(manifest))
            browser = playwright.chromium.launch()
            try:
                for motion in ('no-preference', 'reduce'):
                    page = browser.new_page(viewport={'width': 1920, 'height': 1080}, reduced_motion=motion)
                    page.goto(report.as_uri())
                    for width in (1920, 1440, 1280, 1024, 390):
                        page.set_viewport_size({'width': width, 'height': 1080})
                        for unit in manifest['pages']:
                            page.evaluate('(id) => showPage(id)', unit['id'])
                            if motion == 'no-preference':
                                page.evaluate('document.getAnimations().forEach(a=>{a.pause();a.currentTime=110})')
                            self.assert_layout(page, width)
                            if motion == 'no-preference':
                                page.evaluate('document.getAnimations().forEach(a=>a.finish())')
                            self.assert_layout(page, width)
                    page.close()
            finally:
                browser.close()

    def assert_layout(self, page, width):
        panel = page.locator('.acceptance-view:visible .controls').bounding_box()
        visual = page.locator('.acceptance-view:visible .visual-column').bounding_box()
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        if width > 1200:
            self.assertAlmostEqual(panel['y'], 0, delta=1)
            self.assertAlmostEqual(panel['x'] + panel['width'], width, delta=1)
            self.assertGreaterEqual(panel['x'], visual['x'] + visual['width'])
        else:
            self.assertGreaterEqual(panel['y'], visual['y'] + visual['height'] - 16)


if __name__ == '__main__':
    unittest.main()
