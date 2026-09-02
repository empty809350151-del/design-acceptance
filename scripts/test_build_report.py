#!/usr/bin/env python3
"""Regression checks for the fixed acceptance-report visual system."""

from __future__ import annotations

import importlib.util
import json
import re
import unittest
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
            "font:17px/1.4 Geist",
            "padding-left:220px",
            "width:220px",
            "width:min(100%,32vh,360px)",
            "--green:#22ad01",
            'class="review-title-suffix"',
            'class="sidebar-content"',
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


if __name__ == "__main__":
    unittest.main()
