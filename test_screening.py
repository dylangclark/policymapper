"""Run with: python -m unittest discover -s . -p 'test_screening.py'."""
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook
import build_network as app

ROOT = Path(__file__).resolve().parent

class ScreeningTests(unittest.TestCase):
    def network(self):
        return app.read_workbook(ROOT / 'bc_adaptation_network_input 1.0.xlsx')

    def workbook(self, path, rows):
        book = Workbook()
        sheet = book.active
        sheet.append(['Title row'])
        sheet.append(['Outcome statement', 'Economic risk', 'Governance risk', 'Government salience', 'Urgency'])
        for row in rows:
            sheet.append(row)
        book.save(path)

    def test_supplied_workbooks_match_all_outcomes_without_changing_connections(self):
        data = self.network()
        old_edges = list(data['edges'])
        app.add_screening(data, ROOT / 'bc_adaptation_outcome_screen 2.0.xlsx')
        self.assertEqual(data['screening_matched'], 73)
        self.assertEqual(data['edges'], old_edges)
        for node in data['nodes']:
            if node['kind'] == 'outcome':
                self.assertEqual(set(node['scores']), set(app.SCREENING_FIELDS))
        self.assertTrue(any('wording is broader' in w for w in data['warnings']))

    def test_reordered_rows_join_by_statement_and_unknowns_remain_distinct(self):
        data = self.network()
        outcomes = [n for n in data['nodes'] if n['kind'] == 'outcome']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'screen.xlsx'
            self.workbook(path, [[outcomes[1]['label'], 3, 'Unknown', 'N/A', None],
                                 [outcomes[0]['label'], 1, 2, 3, 2]])
            app.add_screening(data, path)
        self.assertEqual(outcomes[1]['scores'], dict(economic=3, governance=None, salience='N/A', urgency=None))
        self.assertEqual(outcomes[0]['scores']['economic'], 1)
        self.assertNotIn('scores', outcomes[2])
        self.assertEqual(sum('No screening row' in w for w in data['warnings']), 71)

    def test_bad_scores_labels_and_duplicates_fail(self):
        label = next(n['label'] for n in self.network()['nodes'] if n['kind'] == 'outcome')
        cases = [([[label, 4, 2, 2, 2]], 'invalid screening score'),
                 ([['Unrecognized outcome', 1, 2, 2, 2]], 'outcome not found'),
                 ([[label, 1, 2, 2, 2], [label, 3, 2, 2, 2]], 'duplicate outcome')]
        with tempfile.TemporaryDirectory() as directory:
            for rows, message in cases:
                with self.subTest(message=message):
                    path = Path(directory) / 'screen.xlsx'
                    self.workbook(path, rows)
                    with self.assertRaisesRegex(ValueError, message):
                        app.add_screening(self.network(), path)

if __name__ == '__main__':
    unittest.main()
