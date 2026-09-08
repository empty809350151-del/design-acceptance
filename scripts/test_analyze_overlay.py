"""Behavior checks for capture normalization and scoped analysis."""
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from analyze_overlay import analyze, load_image


class AnalyzeOverlayTest(unittest.TestCase):
    def test_uniform_scale_and_chrome_crop(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.png'
            image = Image.new('RGB', (200, 240), 'red')
            ImageDraw.Draw(image).rectangle((0, 40, 199, 239), fill='white')
            image.save(source)
            normalized = load_image(source, (100, 100), {'source_rect': [0, 40, 200, 240], 'scale': .5})
            self.assertEqual(normalized.size, (100, 100))
            self.assertEqual(normalized.getpixel((0, 0)), (255, 255, 255, 255))
            with self.assertRaises(ValueError):
                load_image(source, (100, 130), {'scale': .5})

    def test_scope_excludes_unrelated_difference_and_rejects_empty_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            design = Image.new('RGB', (64, 64), 'white')
            actual = design.copy()
            ImageDraw.Draw(actual).rectangle((32, 0, 63, 63), fill='black')
            design.save(root / 'design.png'); actual.save(root / 'actual.png')
            config = {'actual': str(root / 'actual.png'), 'design': str(root / 'design.png'),
                      'output_dir': directory, 'slug': 'check', 'viewport': [64, 64],
                      'include_rects': [[0, 0, 32, 64]]}
            result = analyze(config)
            self.assertEqual(result['eligible_pixels'], 32 * 64)
            self.assertEqual(result['pixel_fidelity'], 100)
            self.assertTrue((root / result['images']['actual']).exists())
            config['exclude_rects'] = [[0, 0, 32, 64]]
            with self.assertRaisesRegex(ValueError, 'No eligible pixels'):
                analyze(config)

    def test_changed_wrapping_does_not_use_line_width_for_font_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, width in [('actual', 12), ('design', 24)]:
                image = Image.new('RGB', (64, 64), 'white')
                ImageDraw.Draw(image).rectangle((4, 4, width, 13), fill='black')
                image.save(root / f'{name}.png')
            result = analyze({'actual': str(root / 'actual.png'), 'design': str(root / 'design.png'),
                              'output_dir': directory, 'slug': 'wrap', 'viewport': [64, 64],
                              'fields': [{'name': 'title', 'expected': 20, 'actual_rect': [0, 0, 32, 24],
                                          'design_rect': [0, 0, 32, 24], 'same_wrap': False}]})
            self.assertEqual(result['fields'][0]['delta'], 0)


if __name__ == '__main__':
    unittest.main()
