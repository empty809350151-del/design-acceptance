#!/usr/bin/env python3
"""Regression checks for the fixed acceptance-report visual system."""

from __future__ import annotations

import importlib.util
import base64
import json
import re
import unittest
import tempfile
from html.parser import HTMLParser
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
BUILDER_PATH = SKILL_DIR / "scripts" / "build_report.py"
MANIFEST_PATH = SKILL_DIR / "assets" / "example-manifest.json"


def load_builder():
    spec = importlib.util.spec_from_file_location("acceptance_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load report builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.output = cls.builder.build(manifest)

    def test_fixed_visual_system_is_embedded(self) -> None:
        expected = (
            '--sidebar:320px',
            '--inspector:572px',
            '--green:#0073ff',
            '"PingFang SC"',
            'class="issues-heading"',
            'class="sidebar-content"',
            'class="comparison-stage"',
        )
        for signature in expected:
            with self.subTest(signature=signature):
                self.assertIn(signature, self.output)

    def test_page_navigation_resets_overlay_state(self) -> None:
        self.assertIn("function resetViewModes(view)", self.output)
        self.assertIn("resetViewModes(target);animate(target)", self.output)
        self.assertIn("classList.remove('aligned','difference','show-heat','show-mask')", self.output)

    def test_generated_ids_are_unique(self) -> None:
        ids = re.findall(r'\sid="([^"]+)"', self.output)
        self.assertEqual(len(ids), len(set(ids)))

    def test_short_viewport_keeps_its_real_aspect_ratio(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["pages"][0]["viewport"] = [750, 469]
        output = self.builder.build(manifest)
        self.assertIn('class="overlay-wrap partial"', output)
        self.assertIn('style="aspect-ratio:750/469"', output)
        self.assertIn('viewBox="0 0 750 469"', output)

    def test_side_by_side_has_separate_issue_layers_and_hidden_overlay(self) -> None:
        self.assertIn('class="overlay-panel" hidden', self.output)
        self.assertIn('data-compare="split" class="active"', self.output)
        self.assertIn('.issue-mark{display:none}', self.output)
        actual = self.builder.issue_svg([{'id': 1, 'actual_rect': [1, 2, 3, 4], 'expected_rect': [5, 6, 7, 8]}], 'actual')
        design = self.builder.issue_svg([{'id': 1, 'actual_rect': [1, 2, 3, 4], 'expected_rect': [5, 6, 7, 8]}], 'expected')
        self.assertNotIn('class="expected"', actual)
        self.assertNotIn('class="problem"', design)
        self.assertNotIn('class="badge"', design)

    def test_issue_categories_keep_unknown_issues_and_deduplicate_fonts(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["pages"][0]["issues"][0]["category"] = "size"
        manifest["pages"][0]["issues"][2]["category"] = "future-category"
        output = self.builder.build(manifest)
        self.assertIn('元素尺寸问题<span class="fail">（1项）</span>', output)
        self.assertIn('其他问题<span class="fail">（1项）</span>', output)
        self.assertNotIn('class="issue" data-issue="2"', output)
        self.assertIn('共3项', output)

    def test_duplicate_platform_page_ids_rejected(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest['pages'].append(manifest['pages'][0])
        with self.assertRaisesRegex(ValueError, 'unique'):
            self.builder.build(manifest)

    def test_shared_report_survives_without_source_images(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
        original = (SKILL_DIR / 'assets' / 'figma-logo.png').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / '截图.png'
            source.write_bytes(original)
            manifest['pages'][0]['images'] = dict(actual=source.name, design=str(source), heatmap=source.as_uri(), mask=source.name)
            output = self.builder.build(manifest, asset_dir=root)
            received = root / 'recipient' / '验收报告.html'
            received.parent.mkdir()
            received.write_text(output, encoding='utf-8')
            source.unlink()
            report = received.read_text(encoding='utf-8')
            self.assertNotIn(str(source), report)
            self.assertEqual(manifest['pages'][0]['images']['actual'], source.name)
            expected = 'data:image/png;base64,' + base64.b64encode(original).decode('ascii')
            self.assertIn(expected, report)
            class ImageSources(HTMLParser):
                def __init__(self):
                    super().__init__(); self.sources = []
                def handle_starttag(self, tag, attrs):
                    if tag == 'img':
                        self.sources.append(dict(attrs)['src'])
            parsed = ImageSources(); parsed.feed(report)
            self.assertTrue(parsed.sources)
            for image in parsed.sources:
                self.assertTrue(image.startswith('data:image/'))
                self.assertTrue(base64.b64decode(image.split(',', 1)[1], validate=True))
            self.assertNotRegex(report, r'<script[^>]+src=')
            self.assertNotIn('@import', report)

    def test_sharing_rejects_missing_and_remote_screenshots(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as directory:
            manifest['pages'][0]['images']['actual'] = 'missing.png'
            with self.assertRaises(FileNotFoundError):
                self.builder.build(manifest, asset_dir=Path(directory))
        manifest['pages'][0]['images']['actual'] = 'https://example.com/temporary.png'
        with self.assertRaisesRegex(ValueError, 'download remote images first'):
            self.builder.build(manifest)

    def test_embedded_screenshots_are_preserved_and_validated(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
        uri = 'data:image/png;base64,' + base64.b64encode((SKILL_DIR / 'assets' / 'figma-logo.png').read_bytes()).decode('ascii')
        manifest['pages'][0]['images']['actual'] = uri
        self.assertIn(uri, self.builder.build(manifest))
        manifest['pages'][0]['images']['actual'] = 'data:image/svg+xml;base64,PHN2Zz4='
        with self.assertRaisesRegex(ValueError, 'raster'):
            self.builder.build(manifest)


if __name__ == "__main__":
    unittest.main()
