import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fleet_rules as rules  # noqa: E402


class ReviewVerdict(unittest.TestCase):
    def test_open_item_needs_fixes(self):
        self.assertEqual(rules.review_verdict('# Reviewer\n\n### Issues to Fix\n\n- [ ] x (rule: y)\n'), 'fixes')

    def test_no_open_item_is_clean(self):
        self.assertEqual(rules.review_verdict('# Reviewer\n\n### Issues to Fix\n\n- [x] x (rule: y)\n'), 'clean')
        self.assertEqual(rules.review_verdict('# Reviewer\n\n## Issues to Fix\n\nNone.\n'), 'clean')

    def test_no_section_gives_no_verdict(self):
        self.assertEqual(rules.review_verdict('# Reviewer\n\n### Blocking\n\n- [ ] x\n'), '')


if __name__ == '__main__':
    unittest.main()
