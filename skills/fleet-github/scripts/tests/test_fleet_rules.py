import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fleet_rules as r  # noqa: E402

SELF_CHECK = ('Failure: `python - <<PY` -> BLOCKED (script execution via heredoc)\n'
              'Own cause ruled out: my last commit only touched docs\n'
              'Tried: session search found the same command approved at 14:02; lesson search: no lesson matches; '
              'script file route also blocked\n'
              'Claim: headless turns refuse this command class, shown by the BLOCKED line above\n')


class Review(unittest.TestCase):
    def test_grounded_items_pass(self):
        body = ('# Reviewer\n\n### Issues to Fix\n\n'
                '- [ ] Stair corner missing for wall+floor (criterion: "corner forms for wall+floor pair")\n'
                '- [ ] Comment on Resolve() is stale (rule: docs/code-comments.md)\n'
                '- [ ] Placement on top face now faces player (breakage: probe on base ok, head wrong)\n')
        self.assertEqual(r.review_problems(body), [])

    def test_ungrounded_item_is_refused(self):
        body = '# Reviewer\n\n### Issues to Fix\n\n- [ ] Stairs against a wall look wrong\n'
        self.assertTrue(any('grounds' in p for p in r.review_problems(body)))

    def test_old_headings_are_refused(self):
        for heading in ('### Blocking', '### Should-fix', '### Nits'):
            body = f'# Reviewer\n\n{heading}\n\n- [ ] x (rule: y)\n'
            self.assertTrue(r.review_problems(body), heading)

    def test_spec_questions_do_not_belong_in_a_review(self):
        body = '# Reviewer\n\n### Spec questions\n\n- should it also connect upside down?\n'
        self.assertTrue(any('Advisor' in p for p in r.review_problems(body)))

    def test_open_items_mean_changes_requested(self):
        self.assertTrue(r.has_open_issues('### Issues to Fix\n\n- [ ] a (rule: b)\n'))
        self.assertFalse(r.has_open_issues('### Issues to Fix\n\n- [x] a (rule: b)\n'))


class Comment(unittest.TestCase):
    def test_signed_short_comment_passes(self):
        self.assertEqual(r.comment_problems('# Worker-3\n\nDecision: split #133, reason below.\n', '# Worker-3'), [])

    def test_ack_opener_is_refused(self):
        self.assertTrue(r.comment_problems('# Worker-1\n\nAck. Taking the rest in order.\n', '# Worker-1'))
        self.assertTrue(r.comment_problems('# Worker-1\n\n**Noted** — will do.\n', '# Worker-1'))

    def test_long_text_outside_details_is_refused(self):
        body = '# Worker-1\n\n' + 'word ' * 500
        self.assertTrue(any('characters' in p for p in r.comment_problems(body, '# Worker-1')))

    def test_median_length_post_passes(self):
        self.assertEqual(r.comment_problems('# Worker-1\n\n' + 'word ' * 300, '# Worker-1'), [])

    def test_long_evidence_inside_details_is_fine(self):
        body = '# Worker-1\n\nCause found.\n\n<details><summary>Evidence</summary>\n\n' + 'log ' * 600 + '\n</details>\n'
        self.assertEqual(r.comment_problems(body, '# Worker-1'), [])

    def test_honest_gap_statement_is_not_refused(self):
        body = '# Worker-5\n\nI cannot rule out the altitude; the suite did not run at this head.\n'
        self.assertEqual(r.comment_problems(body, '# Worker-5'), [])

    def test_local_paths_are_refused(self):
        self.assertTrue(r.comment_problems('# Worker-2\n\nlog at F:/Unity/x.log\n', '# Worker-2'))


class SelfCheck(unittest.TestCase):
    def test_complete_self_check_passes(self):
        self.assertEqual(r.self_check_problems(SELF_CHECK), [])

    def test_missing_line_is_named(self):
        problems = r.self_check_problems(SELF_CHECK.replace('Own cause ruled out', 'Own cause'))
        self.assertTrue(any('Own cause ruled out' in p for p in problems))

    def test_tried_must_show_both_searches(self):
        text = SELF_CHECK.replace('session search found the same command approved at 14:02; ', '')
        self.assertTrue(any('session' in p for p in r.self_check_problems(text)))


ISSUE = '## Goal\n\nx\n\n## Acceptance criteria\n\n- [ ] corner forms\n- [ ] save keeps shape\n\n## Context\n'


class ReadyForReview(unittest.TestCase):
    def test_evidence_line_per_criterion_passes(self):
        pr = '## Evidence\n\n- corner forms: test red at base, green at head\n- save keeps shape: probe equal\n'
        self.assertEqual(r.ready_problems(pr, ISSUE, is_bug=False, comments=[]), [])

    def test_missing_evidence_is_refused(self):
        pr = '## Evidence\n\n- corner forms: test red at base, green at head\n'
        self.assertTrue(r.ready_problems(pr, ISSUE, is_bug=False, comments=[]))

    def test_bug_needs_cause_reproduction_and_approval(self):
        pr = ('Cause: race between neighbour chunks, shown by probe\nReproduction: snow-probe MODE=trees\n\n'
              '## Evidence\n\n- a: x\n- b: y\n')
        self.assertTrue(r.ready_problems(pr, ISSUE, is_bug=True, comments=[]))
        approved = ['# Advisor\n\nApproach approved: neighbour-ready gate.']
        self.assertEqual(r.ready_problems(pr, ISSUE, is_bug=True, comments=approved), [])
        owner = ['Approach approved, go ahead']
        self.assertEqual(r.ready_problems(pr, ISSUE, is_bug=True, comments=owner), [])

    def test_bug_cause_and_reproduction_may_live_in_the_issue_as_sections(self):
        issue = ISSUE + ('\n## Reproduction\n\n1. snow-probe MODE=trees at 4308235\n\n'
                         '## Cause\n\nThe merge lets a snow plan replace a trunk plan, shown by the probe.\n')
        pr = '## What this PR does\n\nx\n\n## Evidence\n\n- a: x\n- b: y\n'
        approved = ['# Advisor\n\nApproach approved: trunk wins the merge.']
        self.assertEqual(r.ready_problems(pr, issue, is_bug=True, comments=approved), [])

    def test_an_unfilled_template_section_does_not_count(self):
        issue = ISSUE + '\n## Reproduction\n\n1. <steps any bot can run>\n\n## Cause\n\n<one sentence>\n'
        pr = '## Evidence\n\n- a: x\n- b: y\n'
        problems = r.ready_problems(pr, issue, is_bug=True, comments=['# Advisor\n\nApproach approved'])
        self.assertEqual(len(problems), 2)


class IssueSide(unittest.TestCase):
    def test_issue_without_a_linked_pr_cannot_wait_for_review(self):
        self.assertTrue(r.linked_pr_problems([]))

    def test_issue_with_a_linked_pr_is_gated_on_that_pr(self):
        self.assertEqual(r.linked_pr_problems([431]), [])


class StartWork(unittest.TestCase):
    def test_plan_and_reviewer_approval_pass(self):
        pr = '## Work plan\n\nPhase_10_Part_2_Plan §5.3: climate pass, files X, evidence per criterion.\n'
        self.assertEqual(r.start_problems(pr, ['# Reviewer\n\nPlan approved: §5.3']), [])

    def test_pr_opened_before_the_plan_gate_is_exempt(self):
        self.assertEqual(r.start_problems('', [], created_at='2026-11-02T10:00:00Z'), [])
        self.assertTrue(r.start_problems('', [], created_at='2026-11-09T10:00:00Z'))

    def test_missing_plan_or_approval_is_refused(self):
        self.assertTrue(r.start_problems('', ['# Reviewer\n\nPlan approved: §5.3']))
        self.assertTrue(r.start_problems('## Work plan\n\nx\n', []))
        self.assertTrue(r.start_problems('## Work plan\n\nx\n', ['# Worker-1\n\nPlan approved: me']))


if __name__ == '__main__':
    unittest.main()
