"""Focused parser and accessible SVG renderer tests."""
import unittest
from xml.etree import ElementTree

from activity import CalendarParser, render


class ActivityTests(unittest.TestCase):
    def test_count_tooltips(self):
        parser = CalendarParser()
        parser.feed('<td id="day" data-date="2026-10-08" data-level="2"></td>'
                    '<tool-tip for="day">12 contributions on October 8th.</tool-tip>')
        self.assertEqual(parser.cells['day']['level'], 2)
        self.assertEqual(parser.tips['day'], '12 contributions on October 8th.')

    def test_missing_calendar_fails_instead_of_inventing_stats(self):
        parser = CalendarParser()
        parser.feed('<html>Unavailable</html>')
        with self.assertRaises(ValueError):
            parser.calendar()

    def test_all_theme_and_size_variants_are_accessible_xml(self):
        # Synthetic renderer fixture, not a claimed live GitHub response.
        days = [{'date': '2026-10-08', 'level': 2, 'count': 12}]
        for dark in (False, True):
            for mobile in (False, True):
                with self.subTest(dark=dark, mobile=mobile):
                    root = ElementTree.fromstring(render(days, 12, 19, dark, mobile))
                    self.assertEqual(root.attrib['role'], 'img')
                    self.assertIn('12 contributions', ''.join(root.itertext()))
                    self.assertNotIn('http://', root.text or '')


if __name__ == '__main__':
    unittest.main()
