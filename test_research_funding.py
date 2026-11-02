import csv
import tempfile
import unittest
from pathlib import Path

from research_funding import add_research


class ResearchFundingTests(unittest.TestCase):
    def source_rows(self):
        with Path(__file__).with_name('research_projects.csv').open(encoding='utf-8-sig', newline='') as f:
            return list(csv.DictReader(f))

    def parse(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'research.csv'
            with path.open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            data = {}
            add_research(data, path)
            return data['research']['records']

    def test_supplied_inventory_and_money_reconcile(self):
        records = self.parse(self.source_rows())
        self.assertEqual(len(records), 186)
        self.assertEqual(sum(r['cents'] or 0 for r in records), 4739809799)
        self.assertEqual(sum(r['cents'] is None for r in records), 1)
        self.assertEqual(sum(r['region']=='bc' and r['university'] for r in records), 47)
        self.assertEqual(sum(r['region'] in ('bc','canada') and r['university'] for r in records), 165)
        self.assertEqual(sum(r['region']=='international' for r in records), 4)
        self.assertEqual(sum(r['region']=='unknown' for r in records), 4)
        self.assertFalse(next(r for r in records if r['institution']=='Research Institute of the McGill University Health Centre')['university'])
        self.assertFalse(next(r for r in records if r['institution']=='University Health Network (Toronto)')['university'])
        canada_awards = [r for r in records if r['region'] in ('bc','canada') and r['university'] and r['basis']=='award']
        self.assertEqual(sum(r['cents'] for r in canada_awards),2356959200)

    def test_no_secondary_outcome_duplication_and_no_annualization(self):
        row = self.source_rows()[0]
        row['Additional linked outcomes'] = 'Second objective; Third objective'
        row['Grant dollar value (CAD)'] = '15,000.50'
        row['Grant dollar value basis'] = 'Published value: Annual northern research supplement; 5 years'
        records = self.parse([row])
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]['cents'],1500050)
        self.assertEqual(records[0]['basis'],'annual')

    def test_invalid_money_duplicate_and_unknown_institution_rejected(self):
        for value in ['-1','NaN','Infinity','abc','1.001','9007199254740992']:
            row = self.source_rows()[0]
            row['Grant dollar value (CAD)'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.parse([row])
        rows=self.source_rows()[:1]
        with self.assertRaisesRegex(ValueError,'duplicate project'):
            self.parse(rows+rows)
        rows[0]['University / lead institution at award']='Unreviewed foreign institution'
        with self.assertRaisesRegex(ValueError,'lookup'):
            self.parse(rows)


if __name__ == '__main__':
    unittest.main()
